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

# import logging
import re
import uuid
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from loguru import logger

from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from pydantic import BaseModel

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
from camel.responses import ChatAgentResponse
from camel.types import (
    ChatCompletion,
    ChatCompletionChunk,
    ModelPlatformType,
    ModelType,
    OpenAIBackendRole,
    RoleType,
)
from camel.utils import (
    func_string_to_callable,
    get_model_encoding,
    get_pydantic_object_schema,
    json_to_function_code,
)

if TYPE_CHECKING:
    from openai import Stream

    from camel.terminators import ResponseTerminator
    from camel.toolkits import FunctionTool


# logger = logging.getLogger(__name__)

# AgentOps decorator setting
try:
    import os

    if os.getenv("AGENTOPS_API_KEY") is not None:
        from agentops import track_agent
    else:
        raise ImportError
except (ImportError, AttributeError):
    from camel.utils import track_agent


class FunctionCallingRecord(BaseModel):
    r"""Historical records of functions called in the conversation.

    Attributes:
        func_name (str): The name of the function being called.
        args (Dict[str, Any]): The dictionary of arguments passed to
            the function.
        result (Any): The execution result of calling this function.
    """

    func_name: str
    args: Dict[str, Any]
    result: Any

    def __str__(self) -> str:
        r"""Overridden version of the string function.

        Returns:
            str: Modified string to represent the function calling.
        """
        return f"Function Execution: {self.func_name}\n" f"\tArgs: {self.args}\n" f"\tResult: {self.result}"

    def as_dict(self) -> dict[str, Any]:
        r"""Returns the function calling record as a dictionary.

        Returns:
            dict[str, Any]: The function calling record as a dictionary.
        """
        return self.model_dump()


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
        tools (List[FunctionTool], optional): List of available
            :obj:`FunctionTool`. (default: :obj:`None`)
        external_tools (List[FunctionTool], optional): List of external tools
            (:obj:`FunctionTool`) bind to one chat agent. When these tools
            are called, the agent will directly return the request instead of
            processing it. (default: :obj:`None`)
        response_terminators (List[ResponseTerminator], optional): List of
            :obj:`ResponseTerminator` bind to one chat agent.
            (default: :obj:`None`)
        scheduling_strategy (str): name of function that defines how to select
            the next model in ModelManager. (default: :str:`round_robin`)
    """

    def __init__(
        self,
        system_message: Optional[Union[BaseMessage, str]] = None,
        model: Optional[Union[BaseModelBackend, List[BaseModelBackend]]] = None,
        memory: Optional[AgentMemory] = None,
        message_window_size: Optional[int] = None,
        token_limit: Optional[int] = None,
        output_language: Optional[str] = None,
        tools: Optional[List[FunctionTool]] = None,
        external_tools: Optional[List[FunctionTool]] = None,
        response_terminators: Optional[List[ResponseTerminator]] = None,
        scheduling_strategy: str = "round_robin",
    ) -> None:
        from copy import deepcopy

        if isinstance(system_message, str):
            system_message = BaseMessage.make_assistant_message(role_name="Assistant", content=system_message)

        self.orig_sys_message: Optional[BaseMessage] = system_message
        self._system_message: Optional[BaseMessage] = system_message
        self.role_name: str = getattr(system_message, "role_name", None) or "assistant"
        self.role_type: RoleType = getattr(system_message, "role_type", None) or RoleType.ASSISTANT
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

        # Tool registration
        external_tools = external_tools or []
        tools = tools or []
        all_tools = tools + external_tools
        self.external_tool_names = [tool.get_function_name() for tool in external_tools]
        self.func_dict = {tool.get_function_name(): tool.func for tool in all_tools}
        self.tool_dict = {tool.get_function_name(): tool for tool in all_tools}
        self._all_tools = all_tools

        # If the user set tools from `ChatAgent`, it will override the
        # configured tools in `BaseModelBackend`.
        if all_tools:
            # logger.warning(
            #     "Overriding the configured tools in `BaseModelBackend` with the tools from `ChatAgent`."
            # )
            tool_schema_list = [tool.get_openai_tool_schema() for tool in all_tools]
            self.model_backend.model_config_dict["tools"] = tool_schema_list
            self.tool_schema_list = tool_schema_list

        from copy import deepcopy

        self.model_config_dict = deepcopy(self.model_backend.model_config_dict)

        self.model_token_limit = token_limit or self.model_backend.token_limit
        context_creator = ScoreBasedContextCreator(
            self.model_backend.token_counter,
            self.model_token_limit,
        )
        self.memory: AgentMemory = memory or ChatHistoryMemory(context_creator, window_size=message_window_size)

        self.output_language: Optional[str] = output_language
        if self.output_language is not None:
            self.set_output_language(self.output_language)

        self.terminated: bool = False
        self.response_terminators = response_terminators or []
        self.init_messages()

        self.tool_prompt_added = False

    # ruff: noqa: E501
    def _generate_tool_prompt(self, tool_schema_list: List[Dict]) -> str:
        r"""Generates a tool prompt based on the provided tool schema list.

        Args:
            tool_schema_list (List[Dict]): A list of dictionaries, each
                containing a tool schema.

        Returns:
            str: A string representing the tool prompt.
        """
        tool_prompts = []

        for tool in tool_schema_list:
            tool_info = tool["function"]
            tool_name = tool_info["name"]
            tool_description = tool_info["description"]
            tool_json = json.dumps(tool_info, indent=4)

            prompt = f"Use the function '{tool_name}' to '{tool_description}':\n{tool_json}\n"
            tool_prompts.append(prompt)

        tool_prompt_str = "\n".join(tool_prompts)

        final_prompt = f'''
    # Tool prompt
    TOOL_PROMPT = f"""
    You have access to the following functions:

    {tool_prompt_str}

    If you choose to call a function ONLY reply in the following format with no
    prefix or suffix:

    <function=example_function_name>{{"example_name": "example_value"}}
    </function>

    Reminder:
    - Function calls MUST follow the specified format, start with <function=
      and end with </function>
    - Required parameters MUST be specified
    - Only call one function at a time
    - Put the entire function call reply on one line
    - If there is no function call available, answer the question like normal 
      with your current knowledge and do not tell the user about function calls
    """
    '''
        return final_prompt

    def _parse_tool_response(self, response: str):
        r"""Parses the tool response to extract the function name and
        arguments.

        Args:
            response (str): The response from the model containing the
                function call.

        Returns:
            Optional[Dict[str, Any]]: The parsed function name and arguments
                if found, otherwise :obj:`None`.
        """
        function_regex = r"<function=(\w+)>(.*?)</function>"
        match = re.search(function_regex, response)

        if match:
            function_name, args_string = match.groups()
            try:
                args = json.loads(args_string)
                return {"function": function_name, "arguments": args}
            except json.JSONDecodeError as error:
                print(f"Error parsing function arguments: {error}")
                return None
        return None

    def reset(self):
        r"""Resets the :obj:`ChatAgent` to its initial state."""
        self.terminated = False
        self.init_messages()
        for terminator in self.response_terminators:
            terminator.reset()

    @property
    def system_message(self) -> Optional[BaseMessage]:
        r"""The getter method for the property :obj:`system_message`.

        Returns:
            Optional[BaseMessage]: The system message of this agent if set,
                else :obj:`None`.
        """
        return self._system_message

    @system_message.setter
    def system_message(self, message: BaseMessage) -> None:
        r"""The setter method for the property :obj:`system_message`.

        Args:
            message (BaseMessage): The message to be set as the
                new system message of this agent.
        """
        self._system_message = message

    def is_tools_added(self) -> bool:
        r"""Whether OpenAI function calling is enabled for this agent.

        Returns:
            bool: Whether OpenAI function calling is enabled for this
                agent, determined by whether the dictionary of tools
                is empty.
        """
        return len(self.func_dict) > 0

    def update_memory(self, message: BaseMessage, role: OpenAIBackendRole) -> None:
        r"""Updates the agent memory with a new message.

        Args:
            message (BaseMessage): The new message to add to the stored
                messages.
            role (OpenAIBackendRole): The backend role type.
        """
        self.memory.write_record(MemoryRecord(message=message, role_at_backend=role))

    def set_output_language(self, output_language: str) -> BaseMessage:
        r"""Sets the output language for the system message. This method
        updates the output language for the system message. The output
        language determines the language in which the output text should be
        generated.

        Args:
            output_language (str): The desired output language.

        Returns:
            BaseMessage: The updated system message object.
        """
        self.output_language = output_language
        language_prompt = "\nRegardless of the input language, " f"you must output text in {output_language}."
        if self.orig_sys_message is not None:
            content = self.orig_sys_message.content + language_prompt
            self._system_message = self.orig_sys_message.create_new_instance(content)
        else:
            self._system_message = BaseMessage.make_assistant_message(
                role_name="Assistant",
                content=language_prompt,
            )

        system_record = MemoryRecord(
            message=self._system_message,
            role_at_backend=OpenAIBackendRole.SYSTEM,
        )
        self.memory.clear()
        self.memory.write_record(system_record)
        return self._system_message

    def get_info(
        self,
        session_id: Optional[str],
        usage: Optional[Dict[str, int]],
        termination_reasons: List[str],
        num_tokens: int,
        tool_calls: List[FunctionCallingRecord],
        external_tool_request: Optional[ChatCompletionMessageToolCall] = None,
    ) -> Dict[str, Any]:
        r"""Returns a dictionary containing information about the chat session.

        Args:
            session_id (str, optional): The ID of the chat session.
            usage (Dict[str, int], optional): Information about the usage of
                the LLM model.
            termination_reasons (List[str]): The reasons for the termination
                of the chat session.
            num_tokens (int): The number of tokens used in the chat session.
            tool_calls (List[FunctionCallingRecord]): The list of function
                calling records, containing the information of called tools.
            external_tool_request
                (Optional[ChatCompletionMessageToolCall], optional):
                The tool calling request of external tools from the model.
                These requests are directly returned to the user instead of
                being processed by the agent automatically.
                (default: :obj:`None`)

        Returns:
            Dict[str, Any]: The chat session information.
        """
        return {
            "id": session_id,
            "usage": usage,
            "termination_reasons": termination_reasons,
            "num_tokens": num_tokens,
            "tool_calls": tool_calls,
            "external_tool_request": external_tool_request,
        }

    def init_messages(self) -> None:
        r"""Initializes the stored messages list with the current system
        message.
        """
        if self._system_message is not None:
            system_record = MemoryRecord(
                message=self._system_message,
                role_at_backend=OpenAIBackendRole.SYSTEM,
            )
            self.memory.clear()
            self.memory.write_record(system_record)
        else:
            self.memory.clear()

    def _transform_function_calling_format(self, openai_messages: List[dict]):
        r"""Used in deepseek-chat backend. It can modify function calling records' format to match the deepseek-chat backend's format."""
        from copy import deepcopy

        _messages = deepcopy(openai_messages)
        modified_messages = []
        for message in _messages:
            if message["role"] == "function":
                new_message = {"role": "tool", "tool_call_id": message["name"], "content": message["content"]}
                modified_messages.append(new_message)
            else:
                modified_messages.append(message)

        return modified_messages

    def record_message(self, message: BaseMessage) -> None:
        r"""Records the externally provided message into the agent memory as if
        it were an answer of the :obj:`ChatAgent` from the backend. Currently,
        the choice of the critic is submitted with this method.

        Args:
            message (BaseMessage): An external message to be recorded in the
                memory.
        """
        self.update_memory(message, OpenAIBackendRole.ASSISTANT)

    def step(
        self,
        input_message: Union[BaseMessage, str],
        response_format: Optional[Type[BaseModel]] = None,
    ) -> ChatAgentResponse:
        r"""Performs a single step in the chat session by generating a response
        to the input message.

        Args:
            input_message (Union[BaseMessage, str]): The input message to the
                agent. For BaseMessage input, its `role` field that specifies
                the role at backend may be either `user` or `assistant` but it
                will be set to `user` anyway since for the self agent any
                incoming message is external. For str input, the `role_name` would be `User`.
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
        from copy import deepcopy

        self.model_backend.model_config_dict = deepcopy(self.model_config_dict)
        self.tool_dict = {tool.get_function_name(): tool for tool in self._all_tools}
        if self.model_backend.model_config_dict.get("response_format") and response_format:
            raise ValueError(
                "The `response_format` parameter cannot be set both in "
                "the model configuration and in the ChatAgent step."
            )

        if isinstance(input_message, str):
            input_message = BaseMessage.make_user_message(role_name="User", content=input_message)

        if "llama" in self.model_type.lower():
            if self.model_backend.model_config_dict.get("tools", None) and not self.tool_prompt_added:
                tool_prompt = self._generate_tool_prompt(self.tool_schema_list)

                tool_sys_msg = BaseMessage.make_assistant_message(
                    role_name="Assistant",
                    content=tool_prompt,
                )

                self.update_memory(tool_sys_msg, OpenAIBackendRole.SYSTEM)
                self.tool_prompt_added = True

            self.update_memory(input_message, OpenAIBackendRole.USER)

            tool_call_records: List[FunctionCallingRecord] = []
            while True:
                # Check if token has exceeded
                try:
                    openai_messages, num_tokens = self.memory.get_context()
                except RuntimeError as e:
                    return self._step_token_exceed(e.args[1], tool_call_records, "max_tokens_exceeded")
                (
                    response,
                    output_messages,
                    finish_reasons,
                    usage_dict,
                    response_id,
                ) = self._step_model_response(openai_messages, num_tokens)
                # If the model response is not a function call, meaning the
                # model has generated a message response, break the loop
                if (
                    not self.is_tools_added()
                    or not isinstance(response, ChatCompletion)
                    or "</function>" not in response.choices[0].message.content  # type: ignore[operator]
                ):
                    break

                parsed_content = self._parse_tool_response(
                    response.choices[0].message.content  # type: ignore[arg-type]
                )

                response.choices[0].message.tool_calls = [
                    ChatCompletionMessageToolCall(
                        id=str(uuid.uuid4()),
                        function=Function(
                            arguments=str(parsed_content["arguments"]).replace("'", '"'),
                            name=str(parsed_content["function"]),
                        ),
                        type="function",
                    )
                ]

                # Check for external tool call
                tool_call_request = response.choices[0].message.tool_calls[0]
                if tool_call_request.function.name in self.external_tool_names:
                    # if model calls an external tool, directly return the
                    # request
                    info = self._step_get_info(
                        output_messages,
                        finish_reasons,
                        usage_dict,
                        response_id,
                        tool_call_records,
                        num_tokens,
                        tool_call_request,
                    )
                    return ChatAgentResponse(
                        msgs=output_messages,
                        terminated=self.terminated,
                        info=info,
                    )

                # Normal function calling
                tool_call_records.append(self._step_tool_call_and_update(response))

            if response_format is not None:
                (
                    output_messages,
                    finish_reasons,
                    usage_dict,
                    response_id,
                    tool_call,
                    num_tokens,
                ) = self._structure_output_with_function(response_format)
                tool_call_records.append(tool_call)

            info = self._step_get_info(
                output_messages,
                finish_reasons,
                usage_dict,
                response_id,
                tool_call_records,
                num_tokens,
            )

            if len(output_messages) == 1:
                # Auto record if the output result is a single message
                self.record_message(output_messages[0])
            else:
                logger.warning(
                    "Multiple messages returned in `step()`, message won't be "
                    "recorded automatically. Please call `record_message()` "
                    "to record the selected message manually."
                )

            return ChatAgentResponse(msgs=output_messages, terminated=self.terminated, info=info)

        else:
            self.update_memory(input_message, OpenAIBackendRole.USER)
            # try:

            tool_call_records: List[FunctionCallingRecord] = []  # type: ignore[no-redef]
            while True:
                # Check if token has exceeded
                try:
                    openai_messages, num_tokens = self.memory.get_context()
                except RuntimeError as e:
                    return self._step_token_exceed(e.args[1], tool_call_records, "max_tokens_exceeded")

                (
                    response,
                    output_messages,
                    finish_reasons,
                    usage_dict,
                    response_id,
                ) = self._step_model_response(openai_messages, num_tokens)
                # If the model response is not a function call, meaning the
                # model has generated a message response, break the loop
                if (
                    not self.is_tools_added()
                    or not isinstance(response, ChatCompletion)
                    or not response.choices[0].message.tool_calls
                ):
                    break

                # Check for external tool call
                tool_call_request = response.choices[0].message.tool_calls[0]

                if tool_call_request.function.name in self.external_tool_names:
                    # if model calls an external tool, directly return the
                    # request
                    info = self._step_get_info(
                        output_messages,
                        finish_reasons,
                        usage_dict,
                        response_id,
                        tool_call_records,
                        num_tokens,
                        tool_call_request,
                    )
                    return ChatAgentResponse(
                        msgs=output_messages,
                        terminated=self.terminated,
                        info=info,
                    )

                # Normal function calling
                tool_call_records.append(self._step_tool_call_and_update(response))

            if response_format is not None and self.model_type.support_native_tool_calling:
                (
                    output_messages,
                    finish_reasons,
                    usage_dict,
                    response_id,
                    tool_call,
                    num_tokens,
                ) = self._structure_output_with_function(response_format)
                tool_call_records.append(tool_call)

            info = self._step_get_info(
                output_messages,
                finish_reasons,
                usage_dict,
                response_id,
                tool_call_records,
                num_tokens,
            )

            if len(output_messages) == 1:
                # Auto record if the output result is a single message
                self.record_message(output_messages[0])
            else:
                logger.warning(
                    "Multiple messages returned in `step()`, message won't be "
                    "recorded automatically. Please call `record_message()` "
                    "to record the selected message manually."
                )

            return ChatAgentResponse(msgs=output_messages, terminated=self.terminated, info=info)

            # except Exception as e:
            #     logger.error(e)
            #     breakpoint()
            #     raise e

    async def step_async(
        self,
        input_message: Union[BaseMessage, str],
        response_format: Optional[Type[BaseModel]] = None,
    ) -> ChatAgentResponse:
        r"""Performs a single step in the chat session by generating a response
        to the input message. This agent step can call async function calls.

        Args:
            input_message (Union[BaseMessage, str]): The input message to the
                agent. For BaseMessage input, its `role` field that specifies
                the role at backend may be either `user` or `assistant` but it
                will be set to `user` anyway since for the self agent any
                incoming message is external. For str input, the `role_name` would be `User`.
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
            input_message = BaseMessage.make_user_message(role_name="User", content=input_message)

        self.update_memory(input_message, OpenAIBackendRole.USER)

        tool_call_records: List[FunctionCallingRecord] = []
        while True:
            try:
                openai_messages, num_tokens = self.memory.get_context()
            except RuntimeError as e:
                return self._step_token_exceed(e.args[1], tool_call_records, "max_tokens_exceeded")

            (
                response,
                output_messages,
                finish_reasons,
                usage_dict,
                response_id,
            ) = self._step_model_response(openai_messages, num_tokens)

            if (
                not self.is_tools_added()
                or not isinstance(response, ChatCompletion)
                or response.choices[0].message.tool_calls is None
            ):
                break

            # Check for external tool call
            tool_call_request = response.choices[0].message.tool_calls[0]
            if tool_call_request.function.name in self.external_tool_names:
                # if model calls an external tool, directly return the request
                info = self._step_get_info(
                    output_messages,
                    finish_reasons,
                    usage_dict,
                    response_id,
                    tool_call_records,
                    num_tokens,
                    tool_call_request,
                )
                return ChatAgentResponse(msgs=output_messages, terminated=self.terminated, info=info)

            # Normal function calling
            tool_call_records.append(await self._step_tool_call_and_update_async(response))

        if response_format is not None and self.model_type.support_native_tool_calling:
            (
                output_messages,
                finish_reasons,
                usage_dict,
                response_id,
                tool_call_record,
                num_tokens,
            ) = self._structure_output_with_function(response_format)
            tool_call_records.append(tool_call_record)

        info = self._step_get_info(
            output_messages,
            finish_reasons,
            usage_dict,
            response_id,
            tool_call_records,
            num_tokens,
        )

        if len(output_messages) == 1:
            # Auto record if the output result is a single message
            self.record_message(output_messages[0])
        else:
            logger.warning(
                "Multiple messages returned in `step()`, message won't be "
                "recorded automatically. Please call `record_message()` to "
                "record the selected message manually."
            )

        return ChatAgentResponse(msgs=output_messages, terminated=self.terminated, info=info)

    def _step_tool_call_and_update(self, response: ChatCompletion) -> FunctionCallingRecord:
        r"""Processes a function call within the chat completion response,
        records the function call in the provided list of tool calls and
        updates the memory of the current agent.

        Args:
            response (ChatCompletion): The response object from the chat
                completion.

        Returns:
            FunctionCallingRecord: The record of calling the function.
        """

        # Perform function calling
        func_assistant_msg, func_result_msg, tool_call_record = self.step_tool_call(response)

        # Update the messages
        self.update_memory(func_assistant_msg, OpenAIBackendRole.ASSISTANT)
        self.update_memory(func_result_msg, OpenAIBackendRole.FUNCTION)

        return tool_call_record

    async def _step_tool_call_and_update_async(self, response: ChatCompletion) -> FunctionCallingRecord:
        (
            func_assistant_msg,
            func_result_msg,
            func_record,
        ) = await self.step_tool_call_async(response)

        self.update_memory(func_assistant_msg, OpenAIBackendRole.ASSISTANT)
        self.update_memory(func_result_msg, OpenAIBackendRole.FUNCTION)

        return func_record

    def _structure_output_with_function(self, response_format: Type[BaseModel]) -> Tuple[
        List[BaseMessage],
        List[str],
        Dict[str, int],
        str,
        FunctionCallingRecord,
        int,
    ]:
        r"""Internal function of structuring the output of the agent based on
        the given output schema.

        Args:
            response_format (Type[BaseModel]): The output schema to use for
                structuring the output.

        Returns:
            Tuple[List[BaseMessage], List[str], Dict[str, int], str,
                FunctionCallingRecord, int]:
                A tuple containing the output messages, finish reasons, usage
                dictionary, response ID, function calling record, and number of
                tokens.
        """
        from camel.toolkits import FunctionTool

        schema_json = get_pydantic_object_schema(response_format)
        func_str = json_to_function_code(schema_json)
        func_callable = func_string_to_callable(func_str)
        func = FunctionTool(func_callable)

        original_func_dict = self.func_dict
        original_model_dict = self.model_backend.model_config_dict

        # Replace the original tools with the structuring function
        self.func_dict = {func.get_function_name(): func.func}
        self.tool_dict = {func.get_function_name(): func}
        self.model_backend.model_config_dict = original_model_dict.copy()
        self.model_backend.model_config_dict["tools"] = [func.get_openai_tool_schema()]
        self.model_backend.model_config_dict["tool_choice"] = "required"

        openai_messages, num_tokens = self.memory.get_context()
        (
            response,
            output_messages,
            finish_reasons,
            usage_dict,
            response_id,
        ) = self._step_model_response(openai_messages, num_tokens)

        if isinstance(response, ChatCompletion):
            tool_call_record = self._step_tool_call_and_update(response)
        else:
            raise ValueError("Structured output is not supported for stream responses.")

        for base_message_item in output_messages:
            base_message_item.content = str(tool_call_record.result)

        # Recover the original tools
        self.func_dict = original_func_dict
        self.model_backend.model_config_dict = original_model_dict

        return (
            output_messages,
            finish_reasons,
            usage_dict,
            response_id,
            tool_call_record,
            num_tokens,
        )

    def _step_model_response(
        self,
        openai_messages: List[OpenAIMessage],
        num_tokens: int,
    ) -> tuple[
        Union[ChatCompletion, Stream],
        List[BaseMessage],
        List[str],
        Dict[str, int],
        str,
    ]:
        r"""Internal function for agent step model response."""

        response = None
        # Obtain the model's response
        for _ in range(len(self.model_backend.models)):
            try:
                response = self.model_backend.run(openai_messages)
                break
            except Exception as exc:
                logger.error(
                    f"An error occurred while running model "
                    f"{self.model_backend.model_type}, "
                    f"index: {self.model_backend.current_model_index}",
                    exc_info=exc,
                )
                continue
        if not response:
            raise ModelProcessingError(
                "Unable to process messages: none of the provided models " "run succesfully."
            )

        # logger.debug(
        #     f"Model {self.model_backend.model_type}, "
        #     f"index {self.model_backend.current_model_index}, "
        #     f"processed these messages: {openai_messages}"
        # )

        if isinstance(response, ChatCompletion):
            output_messages, finish_reasons, usage_dict, response_id = self.handle_batch_response(response)
        else:
            output_messages, finish_reasons, usage_dict, response_id = self.handle_stream_response(
                response, num_tokens
            )
        return (
            response,
            output_messages,
            finish_reasons,
            usage_dict,
            response_id,
        )

    def _step_get_info(
        self,
        output_messages: List[BaseMessage],
        finish_reasons: List[str],
        usage_dict: Dict[str, int],
        response_id: str,
        tool_calls: List[FunctionCallingRecord],
        num_tokens: int,
        external_tool_request: Optional[ChatCompletionMessageToolCall] = None,
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
            tool_calls (List[FunctionCallingRecord]): Records of function calls
                made during this step.
            num_tokens (int): The number of tokens used in this step.
            external_tool_request (Optional[ChatCompletionMessageToolCall]):
                Any external tool request made during this step.
                (default::obj:`None`)

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
        termination = [terminator.is_terminated(output_messages) for terminator in self.response_terminators]
        # Terminate the agent if any of the terminator terminates
        self.terminated, termination_reason = next(
            ((terminated, termination_reason) for terminated, termination_reason in termination if terminated),
            (False, None),
        )
        # For now only retain the first termination reason
        if self.terminated and termination_reason is not None:
            finish_reasons = [termination_reason] * len(finish_reasons)

        info = self.get_info(
            response_id,
            usage_dict,
            finish_reasons,
            num_tokens,
            tool_calls,
            external_tool_request,
        )
        return info

    def handle_batch_response(
        self, response: ChatCompletion
    ) -> Tuple[List[BaseMessage], List[str], Dict[str, int], str]:
        r"""Process a batch response from the model and extract the necessary
        information.

        Args:
            response (dict): Model response.

        Returns:
            tuple: A tuple of list of output `ChatMessage`, list of
                finish reasons, usage dictionary, and response id.
        """
        output_messages: List[BaseMessage] = []
        for choice in response.choices:
            chat_message = BaseMessage(
                role_name=self.role_name,
                role_type=self.role_type,
                meta_dict=dict(),
                content=choice.message.content or "",
                parsed=getattr(choice.message, "parsed", None),
            )
            # Process log probabilities and append to the message meta information
            if choice.logprobs is not None:
                tokens_logprobs = choice.logprobs.content

                if tokens_logprobs is not None:
                    # Extract and structure logprob information
                    logprobs_info = [
                        {
                            "token": token_logprob.token,
                            "logprob": token_logprob.logprob,
                            "top_logprobs": [
                                (top_logprob.token, top_logprob.logprob)
                                for top_logprob in token_logprob.top_logprobs
                            ],
                        }
                        for token_logprob in tokens_logprobs
                    ]
                # Ensure meta_dict exists before adding logprobs info
                if chat_message.meta_dict is None:
                    chat_message.meta_dict = {}
                chat_message.meta_dict["logprobs_info"] = logprobs_info
            # Append the processed chat message to output
            output_messages.append(chat_message)

        finish_reasons = [str(choice.finish_reason) for choice in response.choices]
        usage = self._safe_model_dump(response.usage) if response.usage is not None else {}
        return (
            output_messages,
            finish_reasons,
            usage,
            response.id,
        )

    def _safe_model_dump(self, obj) -> dict:
        r"""Safely dump a Pydantic model to a dictionary.

        This method attempts to use the `model_dump` method if available,
        otherwise it falls back to the `dict` method.

        Args:
            obj: The Pydantic model instance to be dumped.

        Returns:
            dict: A dictionary representation of the Pydantic model.
        """
        # Check if the `model_dump` method exists (Pydantic v2)
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        # Fallback to `dict()` method (Pydantic v1)
        elif hasattr(obj, "dict"):
            return obj.dict()
        else:
            raise TypeError("The object is not a Pydantic model")

    def handle_stream_response(
        self,
        response: Stream[ChatCompletionChunk],
        prompt_tokens: int,
    ) -> Tuple[List[BaseMessage], List[str], Dict[str, int], str]:
        r"""Process a stream response from the model and extract the necessary
        information.

        Args:
            response (dict): Model response.
            prompt_tokens (int): Number of input prompt tokens.

        Returns:
            tuple: A tuple of list of output `ChatMessage`, list of
                finish reasons, usage dictionary, and response id.
        """
        content_dict: defaultdict = defaultdict(lambda: "")
        finish_reasons_dict: defaultdict = defaultdict(lambda: "")
        output_messages: List[BaseMessage] = []
        response_id: str = ""
        # All choices in one response share one role
        for chunk in response:
            response_id = chunk.id
            for choice in chunk.choices:
                index = choice.index
                delta = choice.delta
                if delta.content is not None:
                    # When response has not been stopped
                    # Notice that only the first chunk_dict has the "role"
                    content_dict[index] += delta.content
                if choice.finish_reason:
                    finish_reasons_dict[index] = choice.finish_reason
                    chat_message = BaseMessage(
                        role_name=self.role_name,
                        role_type=self.role_type,
                        meta_dict=dict(),
                        content=content_dict[index],
                    )
                    output_messages.append(chat_message)
        finish_reasons = [finish_reasons_dict[i] for i in range(len(finish_reasons_dict))]
        usage_dict = self.get_usage_dict(output_messages, prompt_tokens)
        return output_messages, finish_reasons, usage_dict, response_id

    def _step_token_exceed(
        self,
        num_tokens: int,
        tool_calls: List[FunctionCallingRecord],
        termination_reason: str,
    ) -> ChatAgentResponse:
        r"""Return trivial response containing number of tokens and information
        of called functions when the number of tokens exceeds.

        Args:
            num_tokens (int): Number of tokens in the messages.
            tool_calls (List[FunctionCallingRecord]): List of information
                objects of functions called in the current step.
            termination_reason (str): String of termination reason.

        Returns:
            ChatAgentResponse: The struct containing trivial outputs and
                information about token number and called functions.
        """
        self.terminated = True
        output_messages: List[BaseMessage] = []

        info = self.get_info(
            None,
            None,
            [termination_reason],
            num_tokens,
            tool_calls,
        )

        return ChatAgentResponse(
            msgs=output_messages,
            terminated=self.terminated,
            info=info,
        )

    def step_tool_call(
        self,
        response: ChatCompletion,
    ) -> Tuple[FunctionCallingMessage, FunctionCallingMessage, FunctionCallingRecord]:
        r"""Execute the function with arguments following the model's response.

        Args:
            response (Dict[str, Any]): The response obtained by calling the
                model.

        Returns:
            tuple: A tuple consisting of two obj:`FunctionCallingMessage`,
                one about the arguments and the other about the execution
                result, and a struct for logging information about this
                function call.
        """
        choice = response.choices[0]
        if choice.message.tool_calls is None:
            raise RuntimeError("Tool call is None")
        func_name = choice.message.tool_calls[0].function.name

        args = json.loads(choice.message.tool_calls[0].function.arguments)
        tool = self.tool_dict[func_name]

        # ! Here, if the agent calls advanced reasoning, provide the chat history
        if func_name == "make_advanced_reasoning":
            reformed_question = f"""
            Please help an assistant to solve reasoning tasks. 
            Here are the chat history between the assistant and the user, which may help you understand the intention of the user and the question:
            <chat_history>{self.memory.get_context()}</chat_history>

            Now please answer the following question:
            <question>{args['question']}</question>
            """
            args["question"] = reformed_question

        result = tool(**args)

        assist_msg = FunctionCallingMessage(
            role_name=self.role_name,
            role_type=self.role_type,
            meta_dict=None,
            content="",
            func_name=func_name,
            args=args,
        )
        func_msg = FunctionCallingMessage(
            role_name=self.role_name,
            role_type=self.role_type,
            meta_dict=None,
            content="",
            func_name=func_name,
            result=result,
        )

        # Record information about this function call
        func_record = FunctionCallingRecord(func_name=func_name, args=args, result=result)
        return assist_msg, func_msg, func_record

    async def step_tool_call_async(
        self,
        response: ChatCompletion,
    ) -> Tuple[FunctionCallingMessage, FunctionCallingMessage, FunctionCallingRecord]:
        r"""Execute the async function with arguments following the model's
        response.

        Args:
            response (Dict[str, Any]): The response obtained by calling the
                model.

        Returns:
            tuple: A tuple consisting of two obj:`FunctionCallingMessage`,
                one about the arguments and the other about the execution
                result, and a struct for logging information about this
                function call.
        """
        # Note that when function calling is enabled, `n` is set to 1.
        choice = response.choices[0]
        if choice.message.tool_calls is None:
            raise RuntimeError("Tool call is None")
        func_name = choice.message.tool_calls[0].function.name

        args = json.loads(choice.message.tool_calls[0].function.arguments)
        tool = self.tool_dict[func_name]
        result = await tool(**args)

        assist_msg = FunctionCallingMessage(
            role_name=self.role_name,
            role_type=self.role_type,
            meta_dict=None,
            content="",
            func_name=func_name,
            args=args,
        )
        func_msg = FunctionCallingMessage(
            role_name=self.role_name,
            role_type=self.role_type,
            meta_dict=None,
            content="",
            func_name=func_name,
            result=result,
        )

        # Record information about this function call
        func_record = FunctionCallingRecord(func_name=func_name, args=args, result=result)
        return assist_msg, func_msg, func_record

    def get_usage_dict(self, output_messages: List[BaseMessage], prompt_tokens: int) -> Dict[str, int]:
        r"""Get usage dictionary when using the stream mode.

        Args:
            output_messages (list): List of output messages.
            prompt_tokens (int): Number of input prompt tokens.

        Returns:
            dict: Usage dictionary.
        """
        encoding = get_model_encoding(self.model_type.value_for_tiktoken)
        completion_tokens = 0
        for message in output_messages:
            completion_tokens += len(encoding.encode(message.content))
        usage_dict = dict(
            completion_tokens=completion_tokens,
            prompt_tokens=prompt_tokens,
            total_tokens=completion_tokens + prompt_tokens,
        )
        return usage_dict

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
        return f"ChatAgent({self.role_name}, {self.role_type}, {self.model_type})"
