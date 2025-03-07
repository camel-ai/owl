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
from collections import deque
from typing import Dict, List, Optional

from camel.agents import (
    ChatAgent,
    TaskCreationAgent,
    TaskPrioritizationAgent,
    TaskSpecifyAgent,
)
from camel.agents.chat_agent import ChatAgentResponse
from camel.generators import SystemMessageGenerator
from camel.logger import get_logger
from camel.messages import BaseMessage
from camel.prompts import TextPrompt
from camel.types import RoleType, TaskType

logger = get_logger(__name__)


class BabyAGI:
    r"""The BabyAGI Agent adapted from `"Task-driven Autonomous Agent"
    <https://github.com/yoheinakajima/babyagi>`_.

    Args:
        assistant_role_name (str): The name of the role played by the
            assistant.
        user_role_name (str): The name of the role played by the user.
        task_prompt (str, optional): A prompt for the task to be performed.
            (default: :obj:`""`)
        task_type (TaskType, optional): The type of task to perform.
            (default: :obj:`TaskType.AI_SOCIETY`)
        max_task_history (int): The maximum number of previous tasks
            information to include in the task agent.
            (default: :obj:10)
        assistant_agent_kwargs (Dict, optional): Additional arguments to pass
            to the assistant agent. (default: :obj:`None`)
        task_specify_agent_kwargs (Dict, optional): Additional arguments to
            pass to the task specify agent. (default: :obj:`None`)
        task_creation_agent_kwargs (Dict, optional): Additional arguments to
            pass to the task creation agent. (default: :obj:`None`)
        task_prioritization_agent_kwargs (Dict, optional): Additional arguments
            to pass to the task prioritization agent. (default: :obj:`None`)
        sys_msg_generator_kwargs (Dict, optional): Additional arguments to
            pass to the system message generator. (default: :obj:`None`)
        extend_task_specify_meta_dict (Dict, optional): A dict to extend the
            task specify meta dict with. (default: :obj:`None`)
        output_language (str, optional): The language to be output by the
            agents. (default: :obj:`None`)
        message_window_size (int, optional): The maximum number of previous
            messages to include in the context window. If `None`, no windowing
            is performed. (default: :obj:`None`)
    """

    def __init__(
        self,
        assistant_role_name: str,
        user_role_name: str,
        task_prompt: str = "",
        task_type: TaskType = TaskType.AI_SOCIETY,
        max_task_history: int = 10,
        assistant_agent_kwargs: Optional[Dict] = None,
        task_specify_agent_kwargs: Optional[Dict] = None,
        task_creation_agent_kwargs: Optional[Dict] = None,
        task_prioritization_agent_kwargs: Optional[Dict] = None,
        sys_msg_generator_kwargs: Optional[Dict] = None,
        extend_task_specify_meta_dict: Optional[Dict] = None,
        output_language: Optional[str] = None,
        message_window_size: Optional[int] = None,
    ) -> None:
        self.task_type = task_type
        self.task_prompt = task_prompt
        self.specified_task_prompt: TextPrompt
        self.init_specified_task_prompt(
            assistant_role_name,
            user_role_name,
            task_specify_agent_kwargs,
            extend_task_specify_meta_dict,
            output_language,
        )

        sys_msg_generator = SystemMessageGenerator(task_type=self.task_type, **(sys_msg_generator_kwargs or {}))

        init_assistant_sys_msg = sys_msg_generator.from_dicts(
            meta_dicts=[
                dict(
                    assistant_role=assistant_role_name,
                    user_role=user_role_name,
                    task=self.specified_task_prompt,
                )
            ],
            role_tuples=[
                (assistant_role_name, RoleType.ASSISTANT),
            ],
        )

        self.assistant_agent: ChatAgent
        self.assistant_sys_msg: Optional[BaseMessage]
        self.task_creation_agent: TaskCreationAgent
        self.task_prioritization_agent: TaskPrioritizationAgent
        self.init_agents(
            init_assistant_sys_msg[0],
            assistant_agent_kwargs,
            task_creation_agent_kwargs,
            task_prioritization_agent_kwargs,
            output_language,
            message_window_size,
        )

        self.subtasks: deque = deque([])
        self.solved_subtasks: List[str] = []
        self.MAX_TASK_HISTORY = max_task_history

    def init_specified_task_prompt(
        self,
        assistant_role_name: str,
        user_role_name: str,
        task_specify_agent_kwargs: Optional[Dict],
        extend_task_specify_meta_dict: Optional[Dict],
        output_language: Optional[str],
    ):
        r"""Use a task specify agent to generate a specified task prompt.
        Generated specified task prompt will be used to replace original
        task prompt. If there is no task specify agent, specified task
        prompt will not be generated.

        Args:
            assistant_role_name (str): The name of the role played by the
                assistant.
            user_role_name (str): The name of the role played by the user.
            task_specify_agent_kwargs (Dict, optional): Additional arguments
                to pass to the task specify agent.
            extend_task_specify_meta_dict (Dict, optional): A dict to extend
                the task specify meta dict with.
            output_language (str, optional): The language to be output by the
                agents.
        """
        task_specify_meta_dict = dict()
        if self.task_type in [TaskType.AI_SOCIETY, TaskType.MISALIGNMENT]:
            task_specify_meta_dict.update(
                dict(
                    assistant_role=assistant_role_name,
                    user_role=user_role_name,
                )
            )
        task_specify_meta_dict.update(extend_task_specify_meta_dict or {})
        task_specify_agent = TaskSpecifyAgent(
            task_type=self.task_type,
            output_language=output_language,
            **(task_specify_agent_kwargs or {}),
        )
        self.specified_task_prompt = task_specify_agent.run(
            self.task_prompt,
            meta_dict=task_specify_meta_dict,
        )

    def init_agents(
        self,
        init_assistant_sys_msg: BaseMessage,
        assistant_agent_kwargs: Optional[Dict],
        task_creation_agent_kwargs: Optional[Dict],
        task_prioritization_agent_kwargs: Optional[Dict],
        output_language: Optional[str],
        message_window_size: Optional[int] = None,
    ):
        r"""Initialize assistant and user agents with their system messages.

        Args:
            init_assistant_sys_msg (BaseMessage): Assistant agent's initial
                system message.
            assistant_agent_kwargs (Dict, optional): Additional arguments to
                pass to the assistant agent.
            task_creation_agent_kwargs (Dict, optional): Additional arguments
                to pass to the task creation agent.
            task_prioritization_agent_kwargs (Dict, optional): Additional
                arguments to pass to the task prioritization agent.
            output_language (str, optional): The language to be output by the
                agents.
            message_window_size (int, optional): The maximum number of previous
                messages to include in the context window. If `None`, no
                windowing is performed. (default: :obj:`None`)
        """
        self.assistant_agent = ChatAgent(
            init_assistant_sys_msg,
            output_language=output_language,
            message_window_size=message_window_size,
            **(assistant_agent_kwargs or {}),
        )
        self.assistant_sys_msg = self.assistant_agent.system_message
        self.assistant_agent.reset()

        self.task_creation_agent = TaskCreationAgent(
            objective=self.specified_task_prompt,
            role_name=getattr(self.assistant_sys_msg, "role_name", None) or "assistant",
            output_language=output_language,
            message_window_size=message_window_size,
            **(task_creation_agent_kwargs or {}),
        )
        self.task_creation_agent.reset()

        self.task_prioritization_agent = TaskPrioritizationAgent(
            objective=self.specified_task_prompt,
            output_language=output_language,
            message_window_size=message_window_size,
            **(task_prioritization_agent_kwargs or {}),
        )
        self.task_prioritization_agent.reset()

    def step(self) -> ChatAgentResponse:
        r"""BabyAGI agent would pull the first task from the task list,
        complete the task based on the context, then creates new tasks and
        re-prioritizes the task list based on the objective and the result of
        the previous task. It returns assistant message.

        Returns:
            ChatAgentResponse: it contains the resulting assistant message,
            whether the assistant agent terminated the conversation,
            and any additional assistant information.

        """
        if not self.subtasks:
            new_subtask_list = self.task_creation_agent.run(task_list=[])
            prioritized_subtask_list = self.task_prioritization_agent.run(new_subtask_list)
            self.subtasks = deque(prioritized_subtask_list)

        task_name = self.subtasks.popleft()
        assistant_msg_msg = BaseMessage.make_user_message(
            role_name=getattr(self.assistant_sys_msg, "role_name", None) or "assistant",
            content=f"{task_name}",
        )

        assistant_response = self.assistant_agent.step(assistant_msg_msg)
        assistant_msg = assistant_response.msgs[0]

        self.solved_subtasks.append(task_name)
        past_tasks = self.solved_subtasks + list(self.subtasks)

        new_subtask_list = self.task_creation_agent.run(task_list=past_tasks[-self.MAX_TASK_HISTORY :])

        if new_subtask_list:
            self.subtasks.extend(new_subtask_list)
            prioritized_subtask_list = self.task_prioritization_agent.run(
                task_list=list(self.subtasks)[-self.MAX_TASK_HISTORY :]
            )
            self.subtasks = deque(prioritized_subtask_list)
        else:
            logger.info("no new tasks")
        assistant_response.info["task_name"] = task_name
        assistant_response.info["subtasks"] = list(self.subtasks)
        if not self.subtasks:
            terminated = True
            assistant_response.info["termination_reasons"] = "All tasks are solved"
            return ChatAgentResponse(
                msgs=[assistant_msg],
                terminated=terminated,
                info=assistant_response.info,
            )
        return ChatAgentResponse(
            msgs=[assistant_msg],
            terminated=assistant_response.terminated,
            info=assistant_response.info,
        )
