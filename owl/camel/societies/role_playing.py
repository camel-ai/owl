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
import logging
from typing import Dict, List, Optional, Sequence, Tuple, Union

from camel.agents import (
    ChatAgent,
    CriticAgent,
    TaskPlannerAgent,
    TaskSpecifyAgent,
)
from camel.generators import SystemMessageGenerator
from camel.human import Human
from camel.messages import BaseMessage
from camel.models import BaseModelBackend
from camel.prompts import TextPrompt
from camel.responses import ChatAgentResponse
from camel.types import RoleType, TaskType

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class RolePlaying:
    r"""Role playing between two agents.

    Args:
        assistant_role_name (str): The name of the role played by the
            assistant.
        user_role_name (str): The name of the role played by the user.
        critic_role_name (str, optional): The name of the role played by the
            critic. Role name with :obj:`"human"` will set critic as a
            :obj:`Human` agent, else will create a :obj:`CriticAgent`.
            (default: :obj:`"critic"`)
        task_prompt (str, optional): A prompt for the task to be performed.
            (default: :obj:`""`)
        with_task_specify (bool, optional): Whether to use a task specify
            agent. (default: :obj:`True`)
        with_task_planner (bool, optional): Whether to use a task planner
            agent. (default: :obj:`False`)
        with_critic_in_the_loop (bool, optional): Whether to include a critic
            in the loop. (default: :obj:`False`)
        critic_criteria (str, optional): Critic criteria for the critic agent.
            If not specified, set the criteria to improve task performance.
        model (BaseModelBackend, optional): The model backend to use for
            generating responses. If specified, it will override the model in
            all agents if not specified in agent-specific kwargs. (default:
            :obj:`OpenAIModel` with `GPT_4O_MINI`)
        task_type (TaskType, optional): The type of task to perform.
            (default: :obj:`TaskType.AI_SOCIETY`)
        assistant_agent_kwargs (Dict, optional): Additional arguments to pass
            to the assistant agent. (default: :obj:`None`)
        user_agent_kwargs (Dict, optional): Additional arguments to pass to
            the user agent. (default: :obj:`None`)
        task_specify_agent_kwargs (Dict, optional): Additional arguments to
            pass to the task specify agent. (default: :obj:`None`)
        task_planner_agent_kwargs (Dict, optional): Additional arguments to
            pass to the task planner agent. (default: :obj:`None`)
        critic_kwargs (Dict, optional): Additional arguments to pass to the
            critic. (default: :obj:`None`)
        sys_msg_generator_kwargs (Dict, optional): Additional arguments to
            pass to the system message generator. (default: :obj:`None`)
        extend_sys_msg_meta_dicts (List[Dict], optional): A list of dicts to
            extend the system message meta dicts with. (default: :obj:`None`)
        extend_task_specify_meta_dict (Dict, optional): A dict to extend the
            task specify meta dict with. (default: :obj:`None`)
        output_language (str, optional): The language to be output by the
            agents. (default: :obj:`None`)
    """

    def __init__(
        self,
        assistant_role_name: str,
        user_role_name: str,
        *,
        critic_role_name: str = "critic",
        task_prompt: str = "",
        with_task_specify: bool = True,
        with_task_planner: bool = False,
        with_critic_in_the_loop: bool = False,
        critic_criteria: Optional[str] = None,
        model: Optional[BaseModelBackend] = None,
        task_type: TaskType = TaskType.AI_SOCIETY,
        assistant_agent_kwargs: Optional[Dict] = None,
        user_agent_kwargs: Optional[Dict] = None,
        task_specify_agent_kwargs: Optional[Dict] = None,
        task_planner_agent_kwargs: Optional[Dict] = None,
        critic_kwargs: Optional[Dict] = None,
        sys_msg_generator_kwargs: Optional[Dict] = None,
        extend_sys_msg_meta_dicts: Optional[List[Dict]] = None,
        extend_task_specify_meta_dict: Optional[Dict] = None,
        output_language: Optional[str] = None,
    ) -> None:
        if model is not None:
            logger.warning(
                "Model provided globally is set for all agents if not" " already specified in agent_kwargs."
            )

        self.with_task_specify = with_task_specify
        self.with_task_planner = with_task_planner
        self.with_critic_in_the_loop = with_critic_in_the_loop
        self.model = model
        self.task_type = task_type
        self.task_prompt = task_prompt

        self.specified_task_prompt: Optional[TextPrompt] = None
        self._init_specified_task_prompt(
            assistant_role_name,
            user_role_name,
            task_specify_agent_kwargs=task_specify_agent_kwargs,
            extend_task_specify_meta_dict=extend_task_specify_meta_dict,
            output_language=output_language,
        )

        self.planned_task_prompt: Optional[TextPrompt] = None
        self._init_planned_task_prompt(
            task_planner_agent_kwargs=task_planner_agent_kwargs,
            output_language=output_language,
        )

        sys_msg_generator = SystemMessageGenerator(
            task_type=self.task_type,
            **(sys_msg_generator_kwargs or {}),
        )

        (
            init_assistant_sys_msg,
            init_user_sys_msg,
            sys_msg_meta_dicts,
        ) = self._get_sys_message_info(
            assistant_role_name,
            user_role_name,
            sys_msg_generator,
            extend_sys_msg_meta_dicts=extend_sys_msg_meta_dicts,
        )

        self.assistant_agent: ChatAgent
        self.user_agent: ChatAgent
        self.assistant_sys_msg: Optional[BaseMessage]
        self.user_sys_msg: Optional[BaseMessage]
        self._init_agents(
            init_assistant_sys_msg,
            init_user_sys_msg,
            assistant_agent_kwargs=assistant_agent_kwargs,
            user_agent_kwargs=user_agent_kwargs,
            output_language=output_language,
        )
        self.critic: Optional[Union[CriticAgent, Human]] = None
        self.critic_sys_msg: Optional[BaseMessage] = None
        self._init_critic(
            sys_msg_generator,
            sys_msg_meta_dicts,
            critic_role_name,
            critic_criteria=critic_criteria,
            critic_kwargs=critic_kwargs,
        )

    def _init_specified_task_prompt(
        self,
        assistant_role_name: str,
        user_role_name: str,
        task_specify_agent_kwargs: Optional[Dict] = None,
        extend_task_specify_meta_dict: Optional[Dict] = None,
        output_language: Optional[str] = None,
    ) -> None:
        r"""Use a task specify agent to generate a specified task prompt.
        Generated specified task prompt will be used to replace original
        task prompt. If there is no task specify agent, specified task
        prompt will not be generated.

        Args:
            assistant_role_name (str): The name of the role played by the
                assistant.
            user_role_name (str): The name of the role played by the user.
            task_specify_agent_kwargs (Dict, optional): Additional arguments
                to pass to the task specify agent. (default: :obj:`None`)
            extend_task_specify_meta_dict (Dict, optional): A dict to extend
                the task specify meta dict with. (default: :obj:`None`)
            output_language (str, optional): The language to be output by the
                agents. (default: :obj:`None`)
        """
        if self.with_task_specify:
            task_specify_meta_dict = dict()
            if self.task_type in [TaskType.AI_SOCIETY, TaskType.MISALIGNMENT]:
                task_specify_meta_dict.update(
                    dict(
                        assistant_role=assistant_role_name,
                        user_role=user_role_name,
                    )
                )
            task_specify_meta_dict.update(extend_task_specify_meta_dict or {})
            if self.model is not None:
                if task_specify_agent_kwargs is None:
                    task_specify_agent_kwargs = {"model": self.model}
                elif "model" not in task_specify_agent_kwargs:
                    task_specify_agent_kwargs.update(dict(model=self.model))
            task_specify_agent = TaskSpecifyAgent(
                task_type=self.task_type,
                output_language=output_language,
                **(task_specify_agent_kwargs or {}),
            )
            self.specified_task_prompt = task_specify_agent.run(
                self.task_prompt,
                meta_dict=task_specify_meta_dict,
            )
            self.task_prompt = self.specified_task_prompt

    def _init_planned_task_prompt(
        self,
        task_planner_agent_kwargs: Optional[Dict] = None,
        output_language: Optional[str] = None,
    ) -> None:
        r"""Use a task plan agent to append a planned task prompt to task
        prompt. The planned task prompt is generated based on the task
        prompt, which can be original task prompt or specified task prompt
        if available. If there is no task plan agent, planned task prompt
        will not be generated.

        Args:
            task_planner_agent_kwargs (Dict, optional): Additional arguments
                to pass to the task planner agent. (default: :obj:`None`)
            output_language (str, optional): The language to be output by the
                agents. (default: :obj:`None`)
        """
        if self.with_task_planner:
            if self.model is not None:
                if task_planner_agent_kwargs is None:
                    task_planner_agent_kwargs = {"model": self.model}
                elif "model" not in task_planner_agent_kwargs:
                    task_planner_agent_kwargs.update(dict(model=self.model))
            task_planner_agent = TaskPlannerAgent(
                output_language=output_language,
                **(task_planner_agent_kwargs or {}),
            )
            self.planned_task_prompt = task_planner_agent.run(self.task_prompt)
            self.task_prompt = f"{self.task_prompt}\n" f"{self.planned_task_prompt}"
        else:
            self.planned_task_prompt = None

    def _get_sys_message_info(
        self,
        assistant_role_name: str,
        user_role_name: str,
        sys_msg_generator: SystemMessageGenerator,
        extend_sys_msg_meta_dicts: Optional[List[Dict]] = None,
    ) -> Tuple[BaseMessage, BaseMessage, List[Dict]]:
        r"""Get initial assistant and user system message with a list of
        system message meta dicts.

        Args:
            assistant_role_name (str): The name of the role played by the
                assistant.
            user_role_name (str): The name of the role played by the user.
            sys_msg_generator (SystemMessageGenerator): A system message
                generator for agents.
            extend_sys_msg_meta_dicts (List[Dict], optional): A list of dicts
                to extend the system message meta dicts with.
                (default: :obj:`None`)

        Returns:
            Tuple[BaseMessage, BaseMessage, List[Dict]]: A tuple containing a
                `BaseMessage` representing the assistant's initial system
                message, a `BaseMessage` representing the user's initial system
                message, and a list of system message meta dicts.
        """
        sys_msg_meta_dicts = [dict(task=self.task_prompt) for _ in range(2)]
        if extend_sys_msg_meta_dicts is None and self.task_type in [
            TaskType.AI_SOCIETY,
            TaskType.MISALIGNMENT,
        ]:
            extend_sys_msg_meta_dicts = [
                dict(
                    assistant_role=assistant_role_name,
                    user_role=user_role_name,
                )
                for _ in range(2)
            ]

        if extend_sys_msg_meta_dicts is not None:
            sys_msg_meta_dicts = [
                {**sys_msg_meta_dict, **extend_sys_msg_meta_dict}
                for sys_msg_meta_dict, extend_sys_msg_meta_dict in zip(
                    sys_msg_meta_dicts, extend_sys_msg_meta_dicts
                )
            ]

        init_assistant_sys_msg, init_user_sys_msg = sys_msg_generator.from_dicts(
            meta_dicts=sys_msg_meta_dicts,
            role_tuples=[
                (assistant_role_name, RoleType.ASSISTANT),
                (user_role_name, RoleType.USER),
            ],
        )
        return init_assistant_sys_msg, init_user_sys_msg, sys_msg_meta_dicts

    def _init_agents(
        self,
        init_assistant_sys_msg: BaseMessage,
        init_user_sys_msg: BaseMessage,
        assistant_agent_kwargs: Optional[Dict] = None,
        user_agent_kwargs: Optional[Dict] = None,
        output_language: Optional[str] = None,
    ) -> None:
        r"""Initialize assistant and user agents with their system messages.

        Args:
            init_assistant_sys_msg (BaseMessage): Assistant agent's initial
                system message.
            init_user_sys_msg (BaseMessage): User agent's initial system
                message.
            assistant_agent_kwargs (Dict, optional): Additional arguments to
                pass to the assistant agent. (default: :obj:`None`)
            user_agent_kwargs (Dict, optional): Additional arguments to
                pass to the user agent. (default: :obj:`None`)
            output_language (str, optional): The language to be output by the
                agents. (default: :obj:`None`)
        """
        if self.model is not None:
            if assistant_agent_kwargs is None:
                assistant_agent_kwargs = {"model": self.model}
            elif "model" not in assistant_agent_kwargs:
                assistant_agent_kwargs.update(dict(model=self.model))
            if user_agent_kwargs is None:
                user_agent_kwargs = {"model": self.model}
            elif "model" not in user_agent_kwargs:
                user_agent_kwargs.update(dict(model=self.model))

        self.assistant_agent = ChatAgent(
            init_assistant_sys_msg,
            output_language=output_language,
            **(assistant_agent_kwargs or {}),
        )
        self.assistant_sys_msg = self.assistant_agent.system_message

        self.user_agent = ChatAgent(
            init_user_sys_msg,
            output_language=output_language,
            **(user_agent_kwargs or {}),
        )
        self.user_sys_msg = self.user_agent.system_message

    def _init_critic(
        self,
        sys_msg_generator: SystemMessageGenerator,
        sys_msg_meta_dicts: List[Dict],
        critic_role_name: str,
        critic_criteria: Optional[str] = None,
        critic_kwargs: Optional[Dict] = None,
    ) -> None:
        r"""Initialize critic agent. If critic role name is :obj:`"human"`,
        create a :obj:`Human` critic agent. Else, create a :obj:`CriticAgent`
        critic agent with specified critic criteria. If the critic criteria
        is not specified, set it to improve task performance.

        Args:
            sys_msg_generator (SystemMessageGenerator): A system message
                generator for agents.
            sys_msg_meta_dicts (list): A list of system message meta dicts.
            critic_role_name (str): The name of the role played by the critic.
            critic_criteria (str, optional): Critic criteria for the
                critic agent. If not specified, set the criteria to
                improve task performance. (default: :obj:`None`)
            critic_kwargs (Dict, optional): Additional arguments to
                pass to the critic. (default: :obj:`None`)
        """
        if self.with_critic_in_the_loop:
            if critic_role_name.lower() == "human":
                self.critic = Human(**(critic_kwargs or {}))
            else:
                critic_criteria = critic_criteria or "improving the task performance"
                critic_msg_meta_dict = dict(
                    critic_role=critic_role_name,
                    criteria=critic_criteria,
                    **sys_msg_meta_dicts[0],
                )
                self.critic_sys_msg = sys_msg_generator.from_dict(
                    critic_msg_meta_dict,
                    role_tuple=(critic_role_name, RoleType.CRITIC),
                )
                if self.model is not None:
                    if critic_kwargs is None:
                        critic_kwargs = {"model": self.model}
                    elif "model" not in critic_kwargs:
                        critic_kwargs.update(dict(model=self.model))
                self.critic = CriticAgent(
                    self.critic_sys_msg,
                    **(critic_kwargs or {}),
                )

    def _reduce_message_options(
        self,
        messages: Sequence[BaseMessage],
    ) -> BaseMessage:
        r"""Processes a sequence of chat messages, returning the processed
        message. If multiple messages are provided and
        `with_critic_in_the_loop` is `False`, raises a `ValueError`.
        If no messages are provided, a `ValueError` will be raised.

        Args:
            messages (Sequence[BaseMessage]): A sequence of `BaseMessage`
                objects to process.

        Returns:
            BaseMessage: A single `BaseMessage` representing the processed
                message.
        """
        if len(messages) == 0:
            raise ValueError("No messages to process.")
        if len(messages) > 1 and not self.with_critic_in_the_loop:
            raise ValueError("Got than one message to process. " f"Num of messages: {len(messages)}.")
        elif self.with_critic_in_the_loop and self.critic is not None:
            critic_response = self.critic.reduce_step(messages)
            processed_msg = critic_response.msg
        else:
            processed_msg = messages[0]

        return processed_msg

    def init_chat(self, init_msg_content: Optional[str] = None) -> BaseMessage:
        r"""Initializes the chat by resetting both of the assistant and user
        agents. Returns an initial message for the role-playing session.

        Args:
            init_msg_content (str, optional): A user-specified initial message.
                Will be sent to the role-playing session as the initial
                message. (default: :obj:`None`)

        Returns:
            BaseMessage: A single `BaseMessage` representing the initial
                message.
        """
        self.assistant_agent.reset()
        self.user_agent.reset()
        default_init_msg_content = (
            "Now start to give me instructions one by one. " "Only reply with Instruction and Input."
        )
        if init_msg_content is None:
            init_msg_content = default_init_msg_content

        # Initialize a message sent by the assistant
        init_msg = BaseMessage.make_assistant_message(
            role_name=getattr(self.assistant_sys_msg, "role_name", None) or "assistant",
            content=init_msg_content,
        )

        return init_msg

    def step(
        self,
        assistant_msg: BaseMessage,
    ) -> Tuple[ChatAgentResponse, ChatAgentResponse]:
        r"""Advances the conversation by taking a message from the assistant,
        processing it using the user agent, and then processing the resulting
        message using the assistant agent. Returns a tuple containing the
        resulting assistant message, whether the assistant agent terminated
        the conversation, and any additional assistant information, as well as
        a tuple containing the resulting user message, whether the user agent
        terminated the conversation, and any additional user information.

        Args:
            assistant_msg: A `BaseMessage` representing the message from the
                assistant.

        Returns:
            Tuple[ChatAgentResponse, ChatAgentResponse]: A tuple containing two
                ChatAgentResponse: the first struct contains the resulting
                assistant message, whether the assistant agent terminated the
                conversation, and any additional assistant information; the
                second struct contains the resulting user message, whether the
                user agent terminated the conversation, and any additional user
                information.
        """
        user_response = self.user_agent.step(assistant_msg)
        if user_response.terminated or user_response.msgs is None:
            return (
                ChatAgentResponse(msgs=[], terminated=False, info={}),
                ChatAgentResponse(
                    msgs=[],
                    terminated=user_response.terminated,
                    info=user_response.info,
                ),
            )
        user_msg = self._reduce_message_options(user_response.msgs)

        # To prevent recording the same memory more than once (once in chat
        # step and once in role play), and the model generates only one
        # response when multi-response support is enabled.
        if "n" in self.user_agent.model_config_dict.keys() and self.user_agent.model_config_dict["n"] > 1:
            self.user_agent.record_message(user_msg)

        assistant_response = self.assistant_agent.step(user_msg)
        if assistant_response.terminated or assistant_response.msgs is None:
            return (
                ChatAgentResponse(
                    msgs=[],
                    terminated=assistant_response.terminated,
                    info=assistant_response.info,
                ),
                ChatAgentResponse(msgs=[user_msg], terminated=False, info=user_response.info),
            )
        assistant_msg = self._reduce_message_options(assistant_response.msgs)

        # To prevent recording the same memory more than once (once in chat
        # step and once in role play), and the model generates only one
        # response when multi-response support is enabled.
        if (
            "n" in self.assistant_agent.model_config_dict.keys()
            and self.assistant_agent.model_config_dict["n"] > 1
        ):
            self.assistant_agent.record_message(assistant_msg)

        return (
            ChatAgentResponse(
                msgs=[assistant_msg],
                terminated=assistant_response.terminated,
                info=assistant_response.info,
            ),
            ChatAgentResponse(
                msgs=[user_msg],
                terminated=user_response.terminated,
                info=user_response.info,
            ),
        )
