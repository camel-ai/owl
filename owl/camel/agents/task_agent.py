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
from typing import Any, Dict, List, Optional, Union

from camel.agents.chat_agent import ChatAgent
from camel.messages import BaseMessage
from camel.models import BaseModelBackend
from camel.prompts import PromptTemplateGenerator, TextPrompt
from camel.types import RoleType, TaskType
from camel.utils import get_task_list

# AgentOps decorator setting
try:
    import os

    if os.getenv("AGENTOPS_API_KEY") is not None:
        from agentops import track_agent
    else:
        raise ImportError
except (ImportError, AttributeError):
    from camel.utils import track_agent


@track_agent(name="TaskSpecifyAgent")
class TaskSpecifyAgent(ChatAgent):
    r"""An agent that specifies a given task prompt by prompting the user to
    provide more details.

    Attributes:
        DEFAULT_WORD_LIMIT (int): The default word limit for the task prompt.
        task_specify_prompt (TextPrompt): The prompt for specifying the task.

    Args:
        model (BaseModelBackend, optional): The model backend to use for
            generating responses. (default: :obj:`OpenAIModel` with
            `GPT_4O_MINI`)
        task_type (TaskType, optional): The type of task for which to generate
            a prompt. (default: :obj:`TaskType.AI_SOCIETY`)
        task_specify_prompt (Union[str, TextPrompt], optional): The prompt for
            specifying the task. (default: :obj:`None`)
        word_limit (int, optional): The word limit for the task prompt.
            (default: :obj:`50`)
        output_language (str, optional): The language to be output by the
            agent. (default: :obj:`None`)
    """

    DEFAULT_WORD_LIMIT = 50

    def __init__(
        self,
        model: Optional[BaseModelBackend] = None,
        task_type: TaskType = TaskType.AI_SOCIETY,
        task_specify_prompt: Optional[Union[str, TextPrompt]] = None,
        word_limit: int = DEFAULT_WORD_LIMIT,
        output_language: Optional[str] = None,
    ) -> None:
        self.task_specify_prompt: Union[str, TextPrompt]
        if task_specify_prompt is None:
            task_specify_prompt_template = PromptTemplateGenerator().get_task_specify_prompt(task_type)

            self.task_specify_prompt = task_specify_prompt_template.format(word_limit=word_limit)
        else:
            self.task_specify_prompt = TextPrompt(task_specify_prompt)

        system_message = BaseMessage(
            role_name="Task Specifier",
            role_type=RoleType.ASSISTANT,
            meta_dict=None,
            content="You can make a task more specific.",
        )

        super().__init__(
            system_message,
            model=model,
            output_language=output_language,
        )

    def run(
        self,
        task_prompt: Union[str, TextPrompt],
        meta_dict: Optional[Dict[str, Any]] = None,
    ) -> TextPrompt:
        r"""Specify the given task prompt by providing more details.

        Args:
            task_prompt (Union[str, TextPrompt]): The original task
                prompt.
            meta_dict (Dict[str, Any], optional): A dictionary containing
                additional information to include in the prompt.
                (default: :obj:`None`)

        Returns:
            TextPrompt: The specified task prompt.
        """
        self.reset()
        task_specify_prompt = self.task_specify_prompt.format(task=task_prompt)

        if meta_dict is not None:
            task_specify_prompt = task_specify_prompt.format(**meta_dict)
        task_msg = BaseMessage.make_user_message(role_name="Task Specifier", content=task_specify_prompt)
        specifier_response = self.step(task_msg)

        if specifier_response.terminated:
            raise RuntimeError("Task specification failed.")
        if len(specifier_response.msgs) == 0:
            raise RuntimeError("Got no specification message.")

        specified_task_msg = specifier_response.msgs[0]

        return TextPrompt(specified_task_msg.content)


@track_agent(name="TaskPlannerAgent")
class TaskPlannerAgent(ChatAgent):
    r"""An agent that helps divide a task into subtasks based on the input
    task prompt.

    Attributes:
        task_planner_prompt (TextPrompt): A prompt for the agent to divide
            the task into subtasks.

    Args:
        model (BaseModelBackend, optional): The model backend to use for
            generating responses. (default: :obj:`OpenAIModel` with
            `GPT_4O_MINI`)
        output_language (str, optional): The language to be output by the
            agent. (default: :obj:`None`)
    """

    def __init__(
        self,
        model: Optional[BaseModelBackend] = None,
        output_language: Optional[str] = None,
    ) -> None:
        self.task_planner_prompt = TextPrompt("Divide this task into subtasks: {task}. Be concise.")
        system_message = BaseMessage(
            role_name="Task Planner",
            role_type=RoleType.ASSISTANT,
            meta_dict=None,
            content="You are a helpful task planner.",
        )

        super().__init__(
            system_message,
            model=model,
            output_language=output_language,
        )

    def run(
        self,
        task_prompt: Union[str, TextPrompt],
    ) -> TextPrompt:
        r"""Generate subtasks based on the input task prompt.

        Args:
            task_prompt (Union[str, TextPrompt]): The prompt for the task to
                be divided into subtasks.

        Returns:
            TextPrompt: A prompt for the subtasks generated by the agent.
        """
        # TODO: Maybe include roles information.
        self.reset()
        task_planner_prompt = self.task_planner_prompt.format(task=task_prompt)

        task_msg = BaseMessage.make_user_message(role_name="Task Planner", content=task_planner_prompt)

        task_response = self.step(task_msg)

        if task_response.terminated:
            raise RuntimeError("Task planning failed.")
        if len(task_response.msgs) == 0:
            raise RuntimeError("Got no task planning message.")

        sub_tasks_msg = task_response.msgs[0]
        return TextPrompt(sub_tasks_msg.content)


@track_agent(name="TaskCreationAgent")
class TaskCreationAgent(ChatAgent):
    r"""An agent that helps create new tasks based on the objective
    and last completed task. Compared to :obj:`TaskPlannerAgent`,
    it's still a task planner, but it has more context information
    like last task and incomplete task list. Modified from
    `BabyAGI <https://github.com/yoheinakajima/babyagi>`_.

    Attributes:
        task_creation_prompt (TextPrompt): A prompt for the agent to
            create new tasks.

    Args:
        role_name (str): The role name of the Agent to create the task.
        objective (Union[str, TextPrompt]): The objective of the Agent to
            perform the task.
        model (BaseModelBackend, optional): The LLM backend to use for
            generating responses. (default: :obj:`OpenAIModel` with
            `GPT_4O_MINI`)
        output_language (str, optional): The language to be output by the
            agent. (default: :obj:`None`)
        message_window_size (int, optional): The maximum number of previous
            messages to include in the context window. If `None`, no windowing
            is performed. (default: :obj:`None`)
        max_task_num (int, optional): The maximum number of planned
            tasks in one round. (default: :obj:3)
    """

    def __init__(
        self,
        role_name: str,
        objective: Union[str, TextPrompt],
        model: Optional[BaseModelBackend] = None,
        output_language: Optional[str] = None,
        message_window_size: Optional[int] = None,
        max_task_num: Optional[int] = 3,
    ) -> None:
        task_creation_prompt = TextPrompt(
            """Create new a task with the following objective: {objective}.
Never forget you are a Task Creator of {role_name}.
You must instruct me based on my expertise and your needs to solve the task.
You should consider past solved tasks and in-progress tasks: {task_list}.
The new created tasks must not overlap with these past tasks.
The result must be a numbered list in the format:

    #. First Task
    #. Second Task
    #. Third Task

You can only give me up to {max_task_num} tasks at a time. \
Each task should be concise, concrete and doable for a {role_name}.
You should make task plan and not ask me questions.
If you think no new tasks are needed right now, write "No tasks to add."
Now start to give me new tasks one by one. No more than three tasks.
Be concrete.
"""
        )

        self.task_creation_prompt = task_creation_prompt.format(
            objective=objective, role_name=role_name, max_task_num=max_task_num
        )
        self.objective = objective

        system_message = BaseMessage(
            role_name="Task Creator",
            role_type=RoleType.ASSISTANT,
            meta_dict=None,
            content="You are a helpful task creator.",
        )

        super().__init__(
            system_message,
            model=model,
            output_language=output_language,
            message_window_size=message_window_size,
        )

    def run(
        self,
        task_list: List[str],
    ) -> List[str]:
        r"""Generate subtasks based on the previous task results and
        incomplete task list.

        Args:
            task_list (List[str]): The completed or in-progress
                tasks which should not overlap with new created tasks.

        Returns:
            List[str]: The new task list generated by the Agent.
        """

        if len(task_list) > 0:
            task_creation_prompt = self.task_creation_prompt.format(task_list=task_list)
        else:
            task_creation_prompt = self.task_creation_prompt.format(task_list="")

        task_msg = BaseMessage.make_user_message(role_name="Task Creator", content=task_creation_prompt)
        task_response = self.step(task_msg)

        if task_response.terminated:
            raise RuntimeError("Task creation failed.")
        if len(task_response.msgs) == 0:
            raise RuntimeError("Got no task creation message.")

        sub_tasks_msg = task_response.msgs[0]
        return get_task_list(sub_tasks_msg.content)


@track_agent(name="TaskPrioritizationAgent")
class TaskPrioritizationAgent(ChatAgent):
    r"""An agent that helps re-prioritize the task list and
    returns numbered prioritized list. Modified from
    `BabyAGI <https://github.com/yoheinakajima/babyagi>`_.

    Attributes:
        task_prioritization_prompt (TextPrompt): A prompt for the agent to
            prioritize tasks.

    Args:
        objective (Union[str, TextPrompt]): The objective of the Agent to
            perform the task.
        model (BaseModelBackend, optional): The LLM backend to use for
            generating responses. (default: :obj:`OpenAIModel` with
            `GPT_4O_MINI`)
        output_language (str, optional): The language to be output by the
            agent. (default: :obj:`None`)
        message_window_size (int, optional): The maximum number of previous
            messages to include in the context window. If `None`, no windowing
            is performed. (default: :obj:`None`)
    """

    def __init__(
        self,
        objective: Union[str, TextPrompt],
        model: Optional[BaseModelBackend] = None,
        output_language: Optional[str] = None,
        message_window_size: Optional[int] = None,
    ) -> None:
        task_prioritization_prompt = TextPrompt(
            """Prioritize the following tasks : {task_list}.
Consider the ultimate objective of you: {objective}.
Tasks should be sorted from highest to lowest priority, where higher-priority \
tasks are those that act as pre-requisites or are more essential for meeting \
the objective. Return one task per line in your response.
Do not remove or modify any tasks.
The result must be a numbered list in the format:

    #. First task
    #. Second task

The entries must be consecutively numbered, starting with 1.
The number of each entry must be followed by a period.
Do not include any headers before your ranked list or follow your list \
with any other output."""
        )

        self.task_prioritization_prompt = task_prioritization_prompt.format(objective=objective)
        self.objective = objective

        system_message = BaseMessage(
            role_name="Task Prioritizer",
            role_type=RoleType.ASSISTANT,
            meta_dict=None,
            content="You are a helpful task prioritizer.",
        )

        super().__init__(
            system_message,
            model=model,
            output_language=output_language,
            message_window_size=message_window_size,
        )

    def run(
        self,
        task_list: List[str],
    ) -> List[str]:
        r"""Prioritize the task list given the agent objective.

        Args:
            task_list (List[str]): The unprioritized tasks of agent.

        Returns:
            List[str]: The new prioritized task list generated by the Agent.
        """
        task_prioritization_prompt = self.task_prioritization_prompt.format(task_list=task_list)

        task_msg = BaseMessage.make_user_message(role_name="Task Prioritizer", content=task_prioritization_prompt)

        task_response = self.step(task_msg)

        if task_response.terminated:
            raise RuntimeError("Task prioritization failed.")
        if len(task_response.msgs) == 0:
            raise RuntimeError("Got no task prioritization message.")

        sub_tasks_msg = task_response.msgs[0]
        return get_task_list(sub_tasks_msg.content)
