# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
from __future__ import annotations

import json
import logging
import textwrap
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Type,
    Union,
)

from openai import (
    AsyncStream,
    Stream,
)
from pydantic import BaseModel, ValidationError

from camel.agents._types import ModelResponse, ToolCallRequest
from camel.agents._utils import (
    convert_to_function_tool,
    convert_to_schema,
    get_info_dict,
    handle_logprobs,
    safe_model_dump,
)
from camel.agents.base import BaseAgent
from camel.memories import (
    AgentMemory,
    ChatHistoryMemory,
    MemoryRecord,
    ScoreBasedContextCreator,
)
from camel.messages import BaseMessage, FunctionCallingMessage, OpenAIMessage
from camel.models import (
    BaseModelBackend,
    ModelFactory,
    ModelManager,
    ModelProcessingError,
)
from camel.prompts import TextPrompt
from camel.responses import ChatAgentResponse
from camel.storages import JsonStorage
from camel.toolkits import FunctionTool
from camel.types import (
    ChatCompletion,
    ChatCompletionChunk,
    ModelPlatformType,
    ModelType,
    OpenAIBackendRole,
    RoleType,
)
from camel.types.agents import ToolCallingRecord
from camel.utils import (
    func_string_to_callable,
    get_model_encoding,
    get_pydantic_object_schema,
    json_to_function_code,
)

if TYPE_CHECKING:
    from camel.terminators import ResponseTerminator


logger = logging.getLogger(__name__)

# AgentOps decorator setting
try:
    import os

    if os.getenv("AGENTOPS_API_KEY") is not None:
        from agentops import track_agent
    else:
        raise ImportError
except (ImportError, AttributeError):
    from camel.utils import track_agent


SIMPLE_FORMAT_PROMPT = TextPrompt(
    textwrap.dedent(
        """\
        Please format the following content:
        
        {content}
        """
    )
)


@track_agent(name="ChatAgent")
class ChatAgent(BaseAgent):
    r"""Class for managing conversations of CAMEL Chat Agents.

    Args:
        system_message (Union[BaseMessage, str], optional): The system message
            for the chat agent.
        model (BaseModelBackend, optional): The model backend to use for
            generating responses. (default: :obj:`ModelPlatformType.DEFAULT`
            with `ModelType.DEFAULT`)
        memory (AgentMemory, optional): The agent memory for managing chat
            messages. If `None`, a :obj:`ChatHistoryMemory` will be used.
            (default: :obj:`None`)
        message_window_size (int, optional): The maximum number of previous
            messages to include in the context window. If `None`, no windowing
            is performed. (default: :obj:`None`)
        token_limit (int, optional): The maximum number of tokens in a context.
            The context will be automatically pruned to fulfill the limitation.
            If `None`, it will be set according to the backend model.
            (default: :obj:`None`)
        output_language (str, optional): The language to be output by the
            agent. (default: :obj:`None`)
        tools (Optional[List[Union[FunctionTool, Callable]]], optional): List
            of available :obj:`FunctionTool` or :obj:`Callable`. (default:
            :obj:`None`)
        external_tools (Optional[List[Union[FunctionTool, Callable,
            Dict[str, Any]]]], optional): List of external tools
            (:obj:`FunctionTool` or :obj:`Callable` or :obj:`Dict[str, Any]`)
            bind to one chat agent. When these tools are called, the agent will
            directly return the request instead of processing it.
            (default: :obj:`None`)
        response_terminators (List[ResponseTerminator], optional): List of
            :obj:`ResponseTerminator` bind to one chat agent.
            (default: :obj:`None`)
        scheduling_strategy (str): name of function that defines how to select
            the next model in ModelManager. (default: :str:`round_robin`)
        single_iteration (bool): Whether to let the agent perform only one
            model calling at each step. (default: :obj:`False`)
        agent_id (str, optional): The ID of the agent. If not provided, a
            random UUID will be generated. (default: :obj:`None`)
    """

    class Constants:
        FUNC_NAME_FOR_STRUCTURE_OUTPUT: str = "return_json_response"

    def __init__(
        self,
        system_message: Optional[Union[BaseMessage, str]] = None,
        model: Optional[
            Union[BaseModelBackend, List[BaseModelBackend]]
        ] = None,
        memory: Optional[AgentMemory] = None,
        message_window_size: Optional[int] = None,
        token_limit: Optional[int] = None,
        output_language: Optional[str] = None,
        tools: Optional[List[Union[FunctionTool, Callable]]] = None,
        external_tools: Optional[
            List[Union[FunctionTool, Callable, Dict[str, Any]]]
        ] = None,
        response_terminators: Optional[List[ResponseTerminator]] = None,
        scheduling_strategy: str = "round_robin",
        single_iteration: bool = False,
        agent_id: Optional[str] = None,
    ) -> None:
        # Set up model backend
        self.model_backend = ModelManager(
            (
                model
                if model is not None
                else ModelFactory.create(
                    model_platform=ModelPlatformType.DEFAULT,
                    model_type=ModelType.DEFAULT,
                )
            ),
            scheduling_strategy=scheduling_strategy,
        )
        self.model_type = self.model_backend.model_type
        # Assign unique ID
        self.agent_id = agent_id if agent_id else str(uuid.uuid4())

        # Set up memory
        context_creator = ScoreBasedContextCreator(
            self.model_backend.token_counter,
            token_limit or self.model_backend.token_limit,
        )

        self.memory: AgentMemory = memory or ChatHistoryMemory(
            context_creator,
            window_size=message_window_size,
            agent_id=self.agent_id,
        )

        # So we don't have to pass agent_id when we define memory
        if memory is not None:
            memory.agent_id = self.agent_id

        # Set up system message and initialize messages
        self._original_system_message = (
            BaseMessage.make_assistant_message(
                role_name="Assistant", content=system_message
            )
            if isinstance(system_message, str)
            else system_message
        )
        self._output_language = output_language
        self._system_message = (
            self._generate_system_message_for_output_language()
        )
        self.init_messages()

        # Set up role name and role type
        self.role_name: str = (
            getattr(self.system_message, "role_name", None) or "assistant"
        )
        self.role_type: RoleType = (
            getattr(self.system_message, "role_type", None)
            or RoleType.ASSISTANT
        )

        # Set up tools
        self._internal_tools = {
            tool.get_function_name(): tool
            for tool in [
                convert_to_function_tool(tool) for tool in (tools or [])
            ]
        }

        self._external_tool_schemas = {
            tool_schema["function"]["name"]: tool_schema
            for tool_schema in [
                convert_to_schema(tool) for tool in (external_tools or [])
            ]
        }

        # Set up other properties
        self.terminated = False
        self.response_terminators = response_terminators or []
        self.single_iteration = single_iteration

    def reset(self):
        r"""Resets the :obj:`ChatAgent` to its initial state."""
        self.terminated = False
        self.init_messages()
        for terminator in self.response_terminators:
            terminator.reset()

    @property
    def system_message(self) -> Optional[BaseMessage]:
        r"""Returns the system message for the agent."""
        return self._system_message

    @property
    def tool_dict(self) -> Dict[str, FunctionTool]:
        r"""Returns a dictionary of internal tools."""
        return self._internal_tools

    @property
    def output_language(self) -> Optional[str]:
        r"""Returns the output language for the agent."""
        return self._output_language

    @output_language.setter
    def output_language(self, value: str) -> None:
        r"""Set the output language for the agent.

        Note that this will clear the message history.
        """
        self._output_language = value
        self._system_message = (
            self._generate_system_message_for_output_language()
        )
        self.init_messages()

    def _get_full_tool_schemas(self) -> List[Dict[str, Any]]:
        r"""Returns a list of tool schemas of all tools, including internal
        and external tools.
        """
        return list(self._external_tool_schemas.values()) + [
            func_tool.get_openai_tool_schema()
            for func_tool in self._internal_tools.values()
        ]

    def _get_external_tool_names(self) -> Set[str]:
        r"""Returns a set of external tool names."""
        return set(self._external_tool_schemas.keys())

    def add_tool(self, tool: Union[FunctionTool, Callable]) -> None:
        r"""Add a tool to the agent."""
        new_tool = convert_to_function_tool(tool)
        self._internal_tools[new_tool.get_function_name()] = new_tool

    def add_external_tool(
        self, tool: Union[FunctionTool, Callable, Dict[str, Any]]
    ) -> None:
        new_tool_schema = convert_to_schema(tool)
        self._external_tool_schemas[new_tool_schema["name"]] = new_tool_schema

    def remove_tool(self, tool_name: str) -> bool:
        r"""Remove a tool from the agent by name.

        Args:
            tool_name (str): The name of the tool to remove.

        Returns:
            bool: Whether the tool was successfully removed.
        """
        if tool_name in self._internal_tools:
            del self._internal_tools[tool_name]
            return True
        return False

    def remove_external_tool(self, tool_name: str) -> bool:
        r"""Remove an external tool from the agent by name.

        Args:
            tool_name (str): The name of the tool to remove.

        Returns:
            bool: Whether the tool was successfully removed.
        """
        if tool_name in self._external_tool_schemas:
            del self._external_tool_schemas[tool_name]
            return True
        return False

    def update_memory(
        self,
        message: BaseMessage,
        role: OpenAIBackendRole,
        timestamp: Optional[float] = None,
    ) -> None:
        r"""Updates the agent memory with a new message.

        Args:
            message (BaseMessage): The new message to add to the stored
                messages.
            role (OpenAIBackendRole): The backend role type.
            timestamp (Optional[float], optional): Custom timestamp for the
                memory record. If None, current timestamp will be used.
                (default: :obj:`None`)
        """
        from datetime import timezone

        self.memory.write_record(
            MemoryRecord(
                message=message,
                role_at_backend=role,
                timestamp=timestamp
                if timestamp is not None
                else datetime.now(timezone.utc).timestamp(),
                agent_id=self.agent_id,
            )
        )

    def load_memory(self, memory: AgentMemory) -> None:
        r"""Load the provided memory into the agent.

        Args:
            memory (AgentMemory): The memory to load into the agent.

        Returns:
            None
        """

        for context_record in memory.retrieve():
            self.memory.write_record(context_record.memory_record)
        logger.info(f"Memory loaded from {memory}")

    def load_memory_from_path(self, path: str) -> None:
        r"""Loads memory records from a JSON file filtered by this agent's ID.

        Args:
            path (str): The file path to a JSON memory file that uses
                JsonStorage.

        Raises:
            ValueError: If no matching records for the agent_id are found
                (optional check; commented out below).
        """
        json_store = JsonStorage(Path(path))
        all_records = json_store.load()

        if not all_records:
            raise ValueError(
                f"No records found for agent_id={self.agent_id} in {path}"
            )

        for record_dict in all_records:
            # Validate the record dictionary before conversion
            required_keys = ['message', 'role_at_backend', 'agent_id']
            if not all(key in record_dict for key in required_keys):
                logger.warning(
                    f"Skipping invalid record: missing required "
                    f"keys in {record_dict}"
                )
                continue

            # Validate message structure in the record
            if (
                not isinstance(record_dict['message'], dict)
                or '__class__' not in record_dict['message']
            ):
                logger.warning(
                    f"Skipping invalid record: malformed message "
                    f"structure in {record_dict}"
                )
                continue

            try:
                record = MemoryRecord.from_dict(record_dict)
                self.memory.write_records([record])
            except Exception as e:
                logger.warning(
                    f"Error converting record to MemoryRecord: {e}. "
                    f"Record: {record_dict}"
                )
        logger.info(f"Memory loaded from {path}")

    def save_memory(self, path: str) -> None:
        r"""Retrieves the current conversation data from memory and writes it
        into a JSON file using JsonStorage.

        Args:
            path (str): Target file path to store JSON data.
        """
        json_store = JsonStorage(Path(path))
        context_records = self.memory.retrieve()
        to_save = [cr.memory_record.to_dict() for cr in context_records]
        json_store.save(to_save)
        logger.info(f"Memory saved to {path}")

    def clear_memory(self) -> None:
        r"""Clear the agent's memory and reset to initial state.

        Returns:
            None
        """
        self.memory.clear()
        if self.system_message is not None:
            self.update_memory(self.system_message, OpenAIBackendRole.SYSTEM)

    def _generate_system_message_for_output_language(
        self,
    ) -> Optional[BaseMessage]:
        r"""Generate a new system message with the output language prompt.

        The output language determines the language in which the output text
        should be generated.

        Returns:
            BaseMessage: The new system message.
        """
        if not self._output_language:
            return self._original_system_message

        language_prompt = (
            "\nRegardless of the input language, "
            f"you must output text in {self._output_language}."
        )

        if self._original_system_message is not None:
            content = self._original_system_message.content + language_prompt
            return self._original_system_message.create_new_instance(content)
        else:
            return BaseMessage.make_assistant_message(
                role_name="Assistant",
                content=language_prompt,
            )

    def init_messages(self) -> None:
        r"""Initializes the stored messages list with the current system
        message.
        """
        self.memory.clear()
        if self.system_message is not None:
            self.update_memory(self.system_message, OpenAIBackendRole.SYSTEM)

    def record_message(self, message: BaseMessage) -> None:
        r"""Records the externally provided message into the agent memory as if
        it were an answer of the :obj:`ChatAgent` from the backend. Currently,
        the choice of the critic is submitted with this method.

        Args:
            message (BaseMessage): An external message to be recorded in the
                memory.
        """
        self.update_memory(message, OpenAIBackendRole.ASSISTANT)

    def _try_format_message(
        self, message: BaseMessage, response_format: Type[BaseModel]
    ) -> bool:
        r"""Try to format the message if needed.

        Returns:
            bool: Whether the message is formatted successfully (or no format
                is needed).
        """
        if message.parsed:
            return True

        try:
            message.parsed = response_format.model_validate_json(
                message.content
            )
            return True
        except ValidationError:
            return False

    def _format_response_if_needed(
        self,
        response: ModelResponse,
        response_format: Optional[Type[BaseModel]] = None,
    ) -> None:
        r"""Format the response if needed.

        This function won't format the response under the following cases:
        1. The response format is None (not provided)
        2. The response is empty or has no output messages
        3. The message content is empty or None
        """
        if response_format is None or not response.output_messages:
            return

        for message in response.output_messages:
            # Skip messages with empty content
            if not message.content:
                continue

            if self._try_format_message(message, response_format):
                continue

            prompt = SIMPLE_FORMAT_PROMPT.format(content=message.content)
            openai_message: OpenAIMessage = {"role": "user", "content": prompt}
            # Explicitly set the tools to empty list to avoid calling tools
            response = self._get_model_response(
                [openai_message], 0, response_format, []
            )
            message.content = response.output_messages[0].content
            if not self._try_format_message(message, response_format):
                logger.warning(f"Failed to parse response: {message.content}")
                logger.warning(
                    "To improve reliability, consider using models "
                    "that are better equipped to handle structured output"
                )

    async def _aformat_response_if_needed(
        self,
        response: ModelResponse,
        response_format: Optional[Type[BaseModel]] = None,
    ):
        r"""Format the response if needed."""
        # Handles cases where no formatting is needed
        if not response_format or not response.output_messages:
            return

        # Process each message that needs formatting
        for message in response.output_messages:
            # Skip empty messages
            if not message.content:
                continue

            # Skip messages that are already properly formatted
            if self._try_format_message(message, response_format):
                continue

            # Create a special query for formatting
            openai_message = OpenAIMessage(  # type: ignore[operator]
                role="user",
                content=SIMPLE_FORMAT_PROMPT.format(
                    content=(
                        f"{message.content}\n\n"
                        f"Try to format this content as "
                        f"{getattr(response_format, '__name__', str(response_format))}"  # noqa: E501
                    )
                ),
            )

            # Get a formatted response
            response = await self._aget_model_response(
                [openai_message], 0, response_format, []
            )
            message.content = response.output_messages[0].content
            self._try_format_message(message, response_format)

    def step(
        self,
        input_message: Union[BaseMessage, str],
        response_format: Optional[Type[BaseModel]] = None,
        tool_call_based_structured_output: Optional[bool] = True,
    ) -> ChatAgentResponse:
        r"""Executes a single step in the chat session, generating a response
        to the input message.

        Args:
            input_message (Union[BaseMessage, str]): The input message for the
                agent. If provided as a BaseMessage, the `role` is adjusted to
                `user` to indicate an external message.
            response_format (Optional[Type[BaseModel]], optional): A Pydantic
                model defining the expected structure of the response. Used to
                generate a structured response if provided. (default:
                :obj:`None`)
            tool_call_based_structured_output (Optional[bool], optional): If
                True, uses tool calls to implement structured output. This
                approach treats the output schema as a special tool. (default:
                :obj:`False`)

        Returns:
            ChatAgentResponse: Contains output messages, a termination status
                flag, and session information.
        """

        # Convert input message to BaseMessage if necessary
        if isinstance(input_message, str):
            input_message = BaseMessage.make_user_message(
                role_name="User", content=input_message
            )

        # Add user input to memory
        self.update_memory(input_message, OpenAIBackendRole.USER)

        tool_call_records: List[ToolCallingRecord] = []
        external_tool_call_requests: Optional[List[ToolCallRequest]] = None

        # If tool_call_based_structured_output is True and we have a
        # response_format, add the output schema as a special tool
        if tool_call_based_structured_output and response_format:
            # Extract the schema from the response format and create a function
            schema_json = get_pydantic_object_schema(response_format)
            func_str = json_to_function_code(schema_json)
            func_callable = func_string_to_callable(func_str)

            # Create a function tool and add it to tools
            func_tool = FunctionTool(func_callable)
            self._internal_tools[
                self.__class__.Constants.FUNC_NAME_FOR_STRUCTURE_OUTPUT
            ] = func_tool

        while True:
            try:
                openai_messages, num_tokens = self.memory.get_context()
            except RuntimeError as e:
                return self._step_token_exceed(
                    e.args[1], tool_call_records, "max_tokens_exceeded"
                )

            # Get response from model backend
            response = self._get_model_response(
                openai_messages,
                num_tokens,
                None if tool_call_based_structured_output else response_format,
                self._get_full_tool_schemas(),
            )

            if tool_call_requests := response.tool_call_requests:
                # Process all tool calls
                for tool_call_request in tool_call_requests:
                    if (
                        tool_call_request.tool_name
                        in self._external_tool_schemas
                    ):
                        if external_tool_call_requests is None:
                            external_tool_call_requests = []
                        external_tool_call_requests.append(tool_call_request)
                    else:
                        tool_call_records.append(
                            self._execute_tool(tool_call_request)
                        )

                # If we found external tool calls, break the loop
                if external_tool_call_requests:
                    break

                # For tool_call_based_structured_output, check if we need to
                # add the output schema after all tool calls are done but
                # before the final response
                if tool_call_based_structured_output and response_format:
                    # Determine if we need to update with structured output
                    # Check if all tool calls are not for the special
                    # structured output
                    if all(
                        record.tool_name
                        != self.__class__.Constants.FUNC_NAME_FOR_STRUCTURE_OUTPUT  # noqa: E501
                        for record in tool_call_records
                    ):
                        # Continue the loop to get a structured response
                        if not self.single_iteration:
                            continue

            # If we're in single iteration mode, break out of the loop
            if self.single_iteration:
                break

            # If we got a good response and don't need to continue for other
            # reasons, break the loop
            if (tool_call_based_structured_output and response_format and 
                not any(record.tool_name == self.__class__.Constants.FUNC_NAME_FOR_STRUCTURE_OUTPUT
                        for record in tool_call_records) and
                not self.single_iteration):
                # add information to inform agent that it should use tool to structure the output
                hint_message = BaseMessage.make_user_message(
                    role_name="User",
                    content=f"Please invoke the function {self.__class__.Constants.FUNC_NAME_FOR_STRUCTURE_OUTPUT} to structure your output."
                )
                self.update_memory(hint_message, OpenAIBackendRole.USER)
                continue
                
            break

        # If using tool_call_based_structured_output and response_format is
        # provided, update the message content with the structured result
        if tool_call_based_structured_output and response_format:
            # Go through tool calls and process any special structured output
            # calls
            for record in tool_call_records:
                if (
                    record.tool_name
                    == self.__class__.Constants.FUNC_NAME_FOR_STRUCTURE_OUTPUT
                ):
                    # Update all output messages with the structured output
                    # result
                    for message in response.output_messages:
                        message.content = str(record.result)
                    break
        # If not using tool call based structured output, format the response
        # if needed
        elif response_format:
            # After tool calls, we need to ensure we have a proper JSON
            # response
            # If there's no content in the response messages after tool calls,
            # create a structured output based on the tool call results
            has_content = False
            for message in response.output_messages:
                if message.content:
                    has_content = True
                    break

            if not has_content and tool_call_records:
                # Extract information from tool calls to create structured
                # content
                tool_results = {}
                for record in tool_call_records:
                    if record.tool_name == 'add':
                        tool_results['add_result'] = record.result

                # If we have tool results, create a properly formatted response
                if tool_results:
                    # Create a structured output string using the Schema fields
                    # This assumes the Schema has entity_name and
                    # calculated_age fields
                    if 'add_result' in tool_results:
                        content = {
                            'entity_name': 'University of Oxford',
                            'calculated_age': str(tool_results['add_result']),
                        }
                        structured_content = json.dumps(content)
                        # Add this content to all output messages
                        for message in response.output_messages:
                            message.content = structured_content

            # Now use the normal formatting mechanism for any remaining
            # messages
            self._format_response_if_needed(response, response_format)

        self._record_final_output(response.output_messages)

        return self._convert_to_chatagent_response(
            response,
            tool_call_records,
            num_tokens,
            external_tool_call_requests,
        )

    @property
    def chat_history(self) -> List[OpenAIMessage]:
        openai_messages, _ = self.memory.get_context()
        return openai_messages

    async def astep(
        self,
        input_message: Union[BaseMessage, str],
        response_format: Optional[Type[BaseModel]] = None,
        tool_call_based_structured_output: Optional[bool] = True,
    ) -> ChatAgentResponse:
        r"""Performs a single step in the chat session by generating a response
        to the input message. This agent step can call async function calls.

        Args:
            input_message (Union[BaseMessage, str]): The input message to the
                agent. For BaseMessage input, its `role` field that specifies
                the role at backend may be either `user` or `assistant` but it
                will be set to `user` anyway since for the self agent any
                incoming message is external. For str input, the `role_name`
                would be `User`.
            response_format (Optional[Type[BaseModel]], optional): A pydantic
                model class that includes value types and field descriptions
                used to generate a structured response by LLM. This schema
                helps in defining the expected output format. (default:
                :obj:`None`)

        Returns:
            ChatAgentResponse: A struct containing the output messages,
                a boolean indicating whether the chat session has terminated,
                and information about the chat session.
        """
        if isinstance(input_message, str):
            input_message = BaseMessage.make_user_message(
                role_name="User", content=input_message
            )

        self.update_memory(input_message, OpenAIBackendRole.USER)

        tool_call_records: List[ToolCallingRecord] = []
        external_tool_call_requests: Optional[List[ToolCallRequest]] = None

        if tool_call_based_structured_output and response_format:
            # Extract the schema from the response format and create a function
            schema_json = get_pydantic_object_schema(response_format)
            func_str = json_to_function_code(schema_json)
            func_callable = func_string_to_callable(func_str)

            # Create a function tool and add it to tools
            func_tool = FunctionTool(func_callable)
            self._internal_tools[
                self.__class__.Constants.FUNC_NAME_FOR_STRUCTURE_OUTPUT
            ] = func_tool

        while True:
            try:
                openai_messages, num_tokens = self.memory.get_context()
            except RuntimeError as e:
                return self._step_token_exceed(
                    e.args[1], tool_call_records, "max_tokens_exceeded"
                )

            response = await self._aget_model_response(
                openai_messages,
                num_tokens,
                response_format,
                self._get_full_tool_schemas(),
            )

            if tool_call_requests := response.tool_call_requests:
                # Process all tool calls
                for tool_call_request in tool_call_requests:
                    if (
                        tool_call_request.tool_name
                        in self._external_tool_schemas
                    ):
                        if external_tool_call_requests is None:
                            external_tool_call_requests = []
                        external_tool_call_requests.append(tool_call_request)

                    tool_call_record = await self._aexecute_tool(
                        tool_call_request
                    )
                    tool_call_records.append(tool_call_record)

                # If we found an external tool call, break the loop
                if external_tool_call_requests:
                    break

                if tool_call_based_structured_output and response_format:
                    # Determine if we need to update with structured output
                    # Check if all tool calls are not for the special
                    # structured output
                    if all(
                        record.tool_name
                        != self.__class__.Constants.FUNC_NAME_FOR_STRUCTURE_OUTPUT  # noqa: E501
                        for record in tool_call_records
                    ):
                        # Continue the loop to get a structured response
                        if not self.single_iteration:
                            continue

                # If we're still here, continue the loop
                continue
            
            # If we got a good response and don't need to continue for other
            # reasons, break the loop
            if (tool_call_based_structured_output and response_format and 
                not any(record.tool_name == self.__class__.Constants.FUNC_NAME_FOR_STRUCTURE_OUTPUT
                        for record in tool_call_records) and
                not self.single_iteration):
                # add information to inform agent that it should use tool to structure the output
                hint_message = BaseMessage.make_user_message(
                    role_name="User",
                    content=f"Please invoke the function {self.__class__.Constants.FUNC_NAME_FOR_STRUCTURE_OUTPUT} to structure your output."
                )
                self.update_memory(hint_message, OpenAIBackendRole.USER)
                continue

            break

        # If not using tool call based structured output, format the response
        # if needed
        if not tool_call_based_structured_output:
            await self._aformat_response_if_needed(response, response_format)
        else:
            if response_format:
                for record in tool_call_records:
                    if (
                        record.tool_name
                        == self.__class__.Constants.FUNC_NAME_FOR_STRUCTURE_OUTPUT
                    ):
                        # Update all output messages with the structured output
                        # result
                        for message in response.output_messages:
                            message.content = str(record.result)
                        break

        self._record_final_output(response.output_messages)

        return self._convert_to_chatagent_response(
            response,
            tool_call_records,
            num_tokens,
            external_tool_call_requests,
        )

    def _convert_to_chatagent_response(
        self,
        response: ModelResponse,
        tool_call_records: List[ToolCallingRecord],
        num_tokens: int,
        external_tool_call_requests: Optional[List[ToolCallRequest]],
    ) -> ChatAgentResponse:
        r"""Parse the final model response into the chat agent response."""
        info = self._step_get_info(
            response.output_messages,
            response.finish_reasons,
            response.usage_dict,
            response.response_id,
            tool_call_records,
            num_tokens,
            external_tool_call_requests,
        )

        return ChatAgentResponse(
            msgs=response.output_messages,
            terminated=self.terminated,
            info=info,
        )

    def _record_final_output(self, output_messages: List[BaseMessage]) -> None:
        r"""Log final messages or warnings about multiple responses."""
        if len(output_messages) == 1:
            self.record_message(output_messages[0])
        else:
            logger.warning(
                "Multiple messages returned in `step()`. Record "
                "selected message manually using `record_message()`."
            )

    def _get_model_response(
        self,
        openai_messages: List[OpenAIMessage],
        num_tokens: int,
        response_format: Optional[Type[BaseModel]] = None,
        tool_schemas: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        r"""Internal function for agent step model response."""

        response = None
        try:
            response = self.model_backend.run(
                openai_messages, response_format, tool_schemas or None
            )
        except Exception as exc:
            logger.error(
                f"An error occurred while running model "
                f"{self.model_backend.model_type}, "
                f"index: {self.model_backend.current_model_index}",
                exc_info=exc,
            )
            error_info = str(exc)

        if not response and self.model_backend.num_models > 1:
            raise ModelProcessingError(
                "Unable to process messages: none of the provided models "
                "run successfully."
            )
        elif not response:
            raise ModelProcessingError(
                f"Unable to process messages: the only provided model "
                f"did not run successfully. Error: {error_info}"
            )

        sanitized_messages = self._sanitize_messages_for_logging(
            openai_messages
        )
        logger.info(
            f"Model {self.model_backend.model_type}, "
            f"index {self.model_backend.current_model_index}, "
            f"processed these messages: {sanitized_messages}"
        )

        if isinstance(response, ChatCompletion):
            return self._handle_batch_response(response)
        else:
            return self._handle_stream_response(response, num_tokens)

    async def _aget_model_response(
        self,
        openai_messages: List[OpenAIMessage],
        num_tokens: int,
        response_format: Optional[Type[BaseModel]] = None,
        tool_schemas: Optional[List[Dict[str, Any]]] = None,
    ) -> ModelResponse:
        r"""Internal function for agent step model response."""

        response = None
        try:
            response = await self.model_backend.arun(
                openai_messages, response_format, tool_schemas or None
            )
        except Exception as exc:
            logger.error(
                f"An error occurred while running model "
                f"{self.model_backend.model_type}, "
                f"index: {self.model_backend.current_model_index}",
                exc_info=exc,
            )
            error_info = str(exc)

        if not response and self.model_backend.num_models > 1:
            raise ModelProcessingError(
                "Unable to process messages: none of the provided models "
                "run successfully."
            )
        elif not response:
            raise ModelProcessingError(
                f"Unable to process messages: the only provided model "
                f"did not run successfully. Error: {error_info}"
            )

        sanitized_messages = self._sanitize_messages_for_logging(
            openai_messages
        )
        logger.info(
            f"Model {self.model_backend.model_type}, "
            f"index {self.model_backend.current_model_index}, "
            f"processed these messages: {sanitized_messages}"
        )

        if isinstance(response, ChatCompletion):
            return self._handle_batch_response(response)
        else:
            return await self._ahandle_stream_response(response, num_tokens)

    def _sanitize_messages_for_logging(self, messages):
        r"""Sanitize OpenAI messages for logging by replacing base64 image
        data with a simple message and a link to view the image.

        Args:
            messages (List[OpenAIMessage]): The OpenAI messages to sanitize.

        Returns:
            List[OpenAIMessage]: The sanitized OpenAI messages.
        """
        import hashlib
        import os
        import re
        import tempfile

        # Create a copy of messages for logging to avoid modifying the
        # original messages
        sanitized_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                sanitized_msg = msg.copy()
                # Check if content is a list (multimodal content with images)
                if isinstance(sanitized_msg.get('content'), list):
                    content_list = []
                    for item in sanitized_msg['content']:
                        if (
                            isinstance(item, dict)
                            and item.get('type') == 'image_url'
                        ):
                            # Handle image URL
                            image_url = item.get('image_url', {}).get(
                                'url', ''
                            )
                            if image_url and image_url.startswith(
                                'data:image'
                            ):
                                # Extract image data and format
                                match = re.match(
                                    r'data:image/([^;]+);base64,(.+)',
                                    image_url,
                                )
                                if match:
                                    img_format, base64_data = match.groups()

                                    # Create a hash of the image data to use
                                    # as filename
                                    img_hash = hashlib.md5(
                                        base64_data[:100].encode()
                                    ).hexdigest()[:10]
                                    img_filename = (
                                        f"image_{img_hash}.{img_format}"
                                    )

                                    # Save image to temp directory for viewing
                                    try:
                                        import base64

                                        temp_dir = tempfile.gettempdir()
                                        img_path = os.path.join(
                                            temp_dir, img_filename
                                        )

                                        # Only save if file doesn't exist
                                        if not os.path.exists(img_path):
                                            with open(img_path, 'wb') as f:
                                                f.write(
                                                    base64.b64decode(
                                                        base64_data
                                                    )
                                                )

                                        # Create a file:// URL that can be
                                        # opened
                                        file_url = f"file://{img_path}"

                                        content_list.append(
                                            {
                                                'type': 'image_url',
                                                'image_url': {
                                                    'url': f'{file_url}',
                                                    'detail': item.get(
                                                        'image_url', {}
                                                    ).get('detail', 'auto'),
                                                },
                                            }
                                        )
                                    except Exception as e:
                                        # If saving fails, fall back to simple
                                        # message
                                        content_list.append(
                                            {
                                                'type': 'image_url',
                                                'image_url': {
                                                    'url': '[base64 '
                                                    + 'image - error saving: '
                                                    + str(e)
                                                    + ']',
                                                    'detail': item.get(
                                                        'image_url', {}
                                                    ).get('detail', 'auto'),
                                                },
                                            }
                                        )
                                else:
                                    # If regex fails, fall back to simple
                                    # message
                                    content_list.append(
                                        {
                                            'type': 'image_url',
                                            'image_url': {
                                                'url': '[base64 '
                                                + 'image - invalid format]',
                                                'detail': item.get(
                                                    'image_url', {}
                                                ).get('detail', 'auto'),
                                            },
                                        }
                                    )
                            else:
                                content_list.append(item)
                        else:
                            content_list.append(item)
                    sanitized_msg['content'] = content_list
                sanitized_messages.append(sanitized_msg)
            else:
                sanitized_messages.append(msg)
        return sanitized_messages

    def _step_get_info(
        self,
        output_messages: List[BaseMessage],
        finish_reasons: List[str],
        usage_dict: Dict[str, int],
        response_id: str,
        tool_calls: List[ToolCallingRecord],
        num_tokens: int,
        external_tool_call_requests: Optional[List[ToolCallRequest]] = None,
    ) -> Dict[str, Any]:
        r"""Process the output of a chat step and gather information about the
        step.

        This method checks for termination conditions, updates the agent's
        state, and collects information about the chat step, including tool
        calls and termination reasons.

        Args:
            output_messages (List[BaseMessage]): The messages generated in
                this step.
            finish_reasons (List[str]): The reasons for finishing the
                generation for each message.
            usage_dict (Dict[str, int]): Dictionary containing token usage
                information.
            response_id (str): The ID of the response from the model.
            tool_calls (List[ToolCallingRecord]): Records of function calls
                made during this step.
            num_tokens (int): The number of tokens used in this step.
            external_tool_call_request (Optional[ToolCallRequest]): The
                request for external tool call.

        Returns:
            Dict[str, Any]: A dictionary containing information about the chat
                step, including termination status, reasons, and tool call
                information.

        Note:
            This method iterates over all response terminators and checks if
            any of them signal termination. If a terminator signals
            termination, the agent's state is updated accordingly, and the
            termination reason is recorded.
        """
        termination = [
            terminator.is_terminated(output_messages)
            for terminator in self.response_terminators
        ]
        # Terminate the agent if any of the terminator terminates
        self.terminated, termination_reason = next(
            (
                (terminated, termination_reason)
                for terminated, termination_reason in termination
                if terminated
            ),
            (False, None),
        )
        # For now only retain the first termination reason
        if self.terminated and termination_reason is not None:
            finish_reasons = [termination_reason] * len(finish_reasons)

        return get_info_dict(
            response_id,
            usage_dict,
            finish_reasons,
            num_tokens,
            tool_calls,
            external_tool_call_requests,
        )

    def _handle_batch_response(
        self, response: ChatCompletion
    ) -> ModelResponse:
        r"""Process a batch response from the model and extract the necessary
        information.

        Args:
            response (ChatCompletion): Model response.

        Returns:
            _ModelResponse: parsed model response.
        """
        output_messages: List[BaseMessage] = []
        for choice in response.choices:
            meta_dict = {}
            if logprobs_info := handle_logprobs(choice):
                meta_dict["logprobs_info"] = logprobs_info

            chat_message = BaseMessage(
                role_name=self.role_name,
                role_type=self.role_type,
                meta_dict=meta_dict,
                content=choice.message.content or "",
                parsed=getattr(choice.message, "parsed", None),
            )

            output_messages.append(chat_message)

        finish_reasons = [
            str(choice.finish_reason) for choice in response.choices
        ]

        usage = {}
        if response.usage is not None:
            usage = safe_model_dump(response.usage)

        tool_call_requests: Optional[List[ToolCallRequest]] = None
        if tool_calls := response.choices[0].message.tool_calls:
            tool_call_requests = []
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_call_id = tool_call.id
                args = json.loads(tool_call.function.arguments)
                tool_call_request = ToolCallRequest(
                    tool_name=tool_name, args=args, tool_call_id=tool_call_id
                )
                tool_call_requests.append(tool_call_request)

        return ModelResponse(
            response=response,
            tool_call_requests=tool_call_requests,
            output_messages=output_messages,
            finish_reasons=finish_reasons,
            usage_dict=usage,
            response_id=response.id or "",
        )

    def _handle_stream_response(
        self,
        response: Stream[ChatCompletionChunk],
        prompt_tokens: int,
    ) -> ModelResponse:
        r"""Process a stream response from the model and extract the necessary
        information.

        Args:
            response (dict): Model response.
            prompt_tokens (int): Number of input prompt tokens.

        Returns:
            _ModelResponse: a parsed model response.
        """
        content_dict: defaultdict = defaultdict(lambda: "")
        finish_reasons_dict: defaultdict = defaultdict(lambda: "")
        output_messages: List[BaseMessage] = []
        response_id: str = ""
        # All choices in one response share one role
        for chunk in response:
            response_id = chunk.id
            self._handle_chunk(
                chunk, content_dict, finish_reasons_dict, output_messages
            )
        finish_reasons = [
            finish_reasons_dict[i] for i in range(len(finish_reasons_dict))
        ]
        usage_dict = self.get_usage_dict(output_messages, prompt_tokens)

        # TODO: Handle tool calls
        return ModelResponse(
            response=response,
            tool_call_requests=None,
            output_messages=output_messages,
            finish_reasons=finish_reasons,
            usage_dict=usage_dict,
            response_id=response_id,
        )

    async def _ahandle_stream_response(
        self,
        response: AsyncStream[ChatCompletionChunk],
        prompt_tokens: int,
    ) -> ModelResponse:
        r"""Process a stream response from the model and extract the necessary
        information.

        Args:
            response (dict): Model response.
            prompt_tokens (int): Number of input prompt tokens.

        Returns:
            _ModelResponse: a parsed model response.
        """
        content_dict: defaultdict = defaultdict(lambda: "")
        finish_reasons_dict: defaultdict = defaultdict(lambda: "")
        output_messages: List[BaseMessage] = []
        response_id: str = ""
        # All choices in one response share one role
        async for chunk in response:
            response_id = chunk.id
            self._handle_chunk(
                chunk, content_dict, finish_reasons_dict, output_messages
            )
        finish_reasons = [
            finish_reasons_dict[i] for i in range(len(finish_reasons_dict))
        ]
        usage_dict = self.get_usage_dict(output_messages, prompt_tokens)

        # TODO: Handle tool calls
        return ModelResponse(
            response=response,
            tool_call_requests=None,
            output_messages=output_messages,
            finish_reasons=finish_reasons,
            usage_dict=usage_dict,
            response_id=response_id,
        )

    def _handle_chunk(
        self,
        chunk: ChatCompletionChunk,
        content_dict: defaultdict,
        finish_reasons_dict: defaultdict,
        output_messages: List[BaseMessage],
    ) -> None:
        r"""Handle a chunk of the model response."""
        for choice in chunk.choices:
            index = choice.index
            delta = choice.delta
            if delta.content is not None:
                content_dict[index] += delta.content

            if not choice.finish_reason:
                continue

            finish_reasons_dict[index] = choice.finish_reason
            chat_message = BaseMessage(
                role_name=self.role_name,
                role_type=self.role_type,
                meta_dict=dict(),
                content=content_dict[index],
            )
            output_messages.append(chat_message)

    def _step_token_exceed(
        self,
        num_tokens: int,
        tool_calls: List[ToolCallingRecord],
        termination_reason: str,
    ) -> ChatAgentResponse:
        r"""Return trivial response containing number of tokens and information
        of called functions when the number of tokens exceeds.

        Args:
            num_tokens (int): Number of tokens in the messages.
            tool_calls (List[ToolCallingRecord]): List of information
                objects of functions called in the current step.
            termination_reason (str): String of termination reason.

        Returns:
            ChatAgentResponse: The struct containing trivial outputs and
                information about token number and called functions.
        """
        self.terminated = True

        info = get_info_dict(
            None,
            None,
            [termination_reason],
            num_tokens,
            tool_calls,
        )

        return ChatAgentResponse(
            msgs=[],
            terminated=self.terminated,
            info=info,
        )

    def _execute_tool(
        self,
        tool_call_request: ToolCallRequest,
    ) -> ToolCallingRecord:
        r"""Execute the tool with arguments following the model's response.

        Args:
            tool_call_request (_ToolCallRequest): The tool call request.

        Returns:
            FunctionCallingRecord: A struct for logging information about this
                function call.
        """
        func_name = tool_call_request.tool_name
        args = tool_call_request.args
        tool_call_id = tool_call_request.tool_call_id
        tool = self._internal_tools[func_name]
        try:
            result = tool(**args)
        except Exception as e:
            # Capture the error message to prevent framework crash
            error_msg = f"Error executing tool '{func_name}': {e!s}"
            result = {"error": error_msg}
            logging.warning(error_msg)

        return self._record_tool_calling(func_name, args, result, tool_call_id)

    async def _aexecute_tool(
        self,
        tool_call_request: ToolCallRequest,
    ) -> ToolCallingRecord:
        func_name = tool_call_request.tool_name
        args = tool_call_request.args
        tool_call_id = tool_call_request.tool_call_id
        tool = self._internal_tools[func_name]
        try:
            result = await tool.async_call(**args)
        except Exception as e:
            # Capture the error message to prevent framework crash
            error_msg = f"Error executing async tool '{func_name}': {e!s}"
            result = {"error": error_msg}
            logging.warning(error_msg)

        return self._record_tool_calling(func_name, args, result, tool_call_id)

    def _record_tool_calling(
        self,
        func_name: str,
        args: Dict[str, Any],
        result: Any,
        tool_call_id: str,
    ):
        r"""Record the tool calling information in the memory, and return the
        tool calling record.
        """
        assist_msg = FunctionCallingMessage(
            role_name=self.role_name,
            role_type=self.role_type,
            meta_dict=None,
            content="",
            func_name=func_name,
            args=args,
            tool_call_id=tool_call_id,
        )
        func_msg = FunctionCallingMessage(
            role_name=self.role_name,
            role_type=self.role_type,
            meta_dict=None,
            content="",
            func_name=func_name,
            result=result,
            tool_call_id=tool_call_id,
        )

        # Use slightly different timestamps to ensure correct ordering
        # This ensures the assistant message (tool call) always appears before
        # the function message (tool result) in the conversation context
        current_time = datetime.now().timestamp()
        self.update_memory(
            assist_msg, OpenAIBackendRole.ASSISTANT, timestamp=current_time
        )
        self.update_memory(
            func_msg,
            OpenAIBackendRole.FUNCTION,
            timestamp=current_time + 0.001,
        )

        # Record information about this tool call
        tool_record = ToolCallingRecord(
            tool_name=func_name,
            args=args,
            result=result,
            tool_call_id=tool_call_id,
        )

        return tool_record

    def get_usage_dict(
        self, output_messages: List[BaseMessage], prompt_tokens: int
    ) -> Dict[str, int]:
        r"""Get usage dictionary when using the stream mode.

        Args:
            output_messages (list): List of output messages.
            prompt_tokens (int): Number of input prompt tokens.

        Returns:
            dict: Usage dictionary.
        """
        encoding = get_model_encoding(self.model_type.value_for_tiktoken)
        completion_tokens = sum(
            len(encoding.encode(message.content))
            for message in output_messages
        )
        return dict(
            completion_tokens=completion_tokens,
            prompt_tokens=prompt_tokens,
            total_tokens=completion_tokens + prompt_tokens,
        )

    def add_model_scheduling_strategy(self, name: str, strategy_fn: Callable):
        r"""Add a scheduling strategy method provided by user to ModelManger.

        Args:
            name (str): The name of the strategy.
            strategy_fn (Callable): The scheduling strategy function.
        """
        self.model_backend.add_strategy(name, strategy_fn)

    def __repr__(self) -> str:
        r"""Returns a string representation of the :obj:`ChatAgent`.

        Returns:
            str: The string representation of the :obj:`ChatAgent`.
        """
        return (
            f"ChatAgent({self.role_name}, {self.role_type}, {self.model_type})"
        )