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

import re
from enum import Enum
from typing import Callable, Dict, List, Literal, Optional, Union

from pydantic import BaseModel

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.prompts import TextPrompt

from .task_prompt import (
    TASK_COMPOSE_PROMPT,
    TASK_DECOMPOSE_PROMPT,
    TASK_EVOLVE_PROMPT,
)
from loguru import logger


def parse_response(response: str, task_id: Optional[str] = None) -> List["Task"]:
    r"""Parse Tasks from a response.

    Args:
        response (str): The model response.
        task_id (str, optional): a parent task id,
            the default value is "0"

    Returns:
        List[Task]: A list of tasks which is :obj:`Task` instance.
    """
    pattern = "<task>(.*?)</task>"
    tasks_content = re.findall(pattern, response, re.DOTALL)

    tasks = []
    if task_id is None:
        task_id = "0"
    for i, content in enumerate(tasks_content):
        tasks.append(Task(content=content.strip(), id=f"{task_id}.{i}"))
    return tasks


class TaskState(str, Enum):
    OPEN = "OPEN"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    DELETED = "DELETED"

    @classmethod
    def states(cls):
        return [s.value for s in cls]


class Task(BaseModel):
    r"""Task is specific assignment that can be passed to a agent.

    Attributes:
        content: string content for task.
        id: An unique string identifier for the task. This should
        ideally be provided by the provider/model which created the task.
        state: The state which should be OPEN, RUNNING, DONE or DELETED.
        type: task type
        parent: The parent task, None for root task.
        subtasks: The childrent sub-tasks for the task.
        result: The answer for the task.
    """

    content: str

    id: str = ""

    state: TaskState = TaskState.OPEN

    type: Optional[str] = None

    parent: Optional["Task"] = None

    subtasks: List["Task"] = []

    result: Optional[str] = ""

    failure_count: int = 0

    failure_reason: str = ""

    failure_info: str = ""

    additional_info: Optional[str] = None

    @classmethod
    def from_message(cls, message: BaseMessage) -> "Task":
        r"""Create a task from a message.

        Args:
            message (BaseMessage): The message to the task.

        Returns:
            Task
        """
        return cls(content=message.content, id="0")

    @staticmethod
    def to_message():
        r"""Convert a Task to a Message."""
        # TODO
        pass

    def reset(self):
        r"""Reset Task to initial state."""
        self.state = TaskState.OPEN
        self.result = ""

    def update_result(self, result: str):
        r"""Set task result and mark the task as DONE.

        Args:
            result (str): The task result.
        """
        self.result = result
        self.set_state(TaskState.DONE)

    def set_id(self, id: str):
        r"""Set the id of the task.

        Args:
            id (str): The id of the task.
        """
        self.id = id

    def set_state(self, state: TaskState):
        r"""Recursively set the state of the task and its subtasks.

        Args:
            state (TaskState): The giving state.
        """
        self.state = state
        if state == TaskState.DONE:
            for subtask in self.subtasks:
                if subtask.state != TaskState.DELETED:
                    subtask.set_state(state)
        elif state == TaskState.RUNNING and self.parent:
            self.parent.set_state(state)

    def add_subtask(self, task: "Task"):
        r"""Add a subtask to the current task.

        Args:
            task (Task): The subtask to be added.
        """
        task.parent = self
        self.subtasks.append(task)

    def remove_subtask(self, id: str):
        r"""Remove a subtask from the current task.

        Args:
            id (str): The id of the subtask to be removed.
        """
        self.subtasks = [task for task in self.subtasks if task.id != id]

    def get_running_task(self) -> Optional["Task"]:
        r"""Get RUNNING task."""
        for sub in self.subtasks:
            if sub.state == TaskState.RUNNING:
                return sub.get_running_task()
        if self.state == TaskState.RUNNING:
            return self
        return None

    def to_string(self, indent: str = "", state: bool = False) -> str:
        r"""Convert task to a sting.

        Args:
            indent (str): The ident for hierarchical tasks.
            state (bool): Include or not task state.

        Returns:
            str: The printable task string.
        """
        if state:
            _str = f"{indent}[{self.state}] Task {self.id}: {self.content}\n"
        else:
            _str = f"{indent}Task {self.id}: {self.content}\n"
        for subtask in self.subtasks:
            _str += subtask.to_string(indent + "  ", state)
        return _str

    def get_result(self, indent: str = "") -> str:
        r"""Get task result to a sting.

        Args:
            indent (str): The ident for hierarchical tasks.

        Returns:
            str: The printable task string.
        """
        _str = f"{indent}Task {self.id} result: {self.result}\n"
        for subtask in self.subtasks:
            _str += subtask.get_result(indent + "  ")
        return _str

    def decompose(
        self,
        agent: ChatAgent,
        prompt: Optional[str] = None,
        task_parser: Callable[[str, str], List["Task"]] = parse_response,
    ) -> List["Task"]:
        r"""Decompose a task to a list of sub-tasks. It can be used for data
        generation and planner of agent.

        Args:
            agent (ChatAgent): An agent that used to decompose the task.
            prompt (str, optional): A prompt to decompose the task. If not
                provided, the default prompt will be used.
            task_parser (Callable[[str, str], List[Task]], optional): A
                function to extract Task from response. If not provided,
                the default parse_response will be used.

        Returns:
            List[Task]: A list of tasks which are :obj:`Task` instances.
        """

        role_name = agent.role_name
        content = prompt or TASK_DECOMPOSE_PROMPT.format(
            role_name=role_name,
            content=self.content,
        )
        msg = BaseMessage.make_user_message(role_name=role_name, content=content)
        response = agent.step(msg)
        tasks = task_parser(response.msg.content, self.id)
        for task in tasks:
            task.additional_info = self.additional_info

        # print decompse result
        for task in tasks:
            logger.info(f"Decompose task {self.id} to {task.id}: {task.content}\n")

        return tasks

    def compose(
        self,
        agent: ChatAgent,
        template: TextPrompt = TASK_COMPOSE_PROMPT,
        result_parser: Optional[Callable[[str], str]] = None,
    ):
        r"""compose task result by the sub-tasks.

        Args:
            agent (ChatAgent): An agent that used to compose the task result.
            template (TextPrompt, optional): The prompt template to compose
                task. If not provided, the default template will be used.
            result_parser (Callable[[str, str], List[Task]], optional): A
                function to extract Task from response.
        """

        if not self.subtasks:
            return

        sub_tasks_result = self.get_result()

        role_name = agent.role_name
        content = template.format(
            role_name=role_name,
            content=self.content,
            additional_info=self.additional_info,
            other_results=sub_tasks_result,
        )
        msg = BaseMessage.make_user_message(role_name=role_name, content=content)
        response = agent.step(msg)
        result = response.msg.content
        if result_parser:
            result = result_parser(result)
        self.update_result(result)

    def get_depth(self) -> int:
        r"""Get current task depth."""
        if self.parent is None:
            return 1
        return 1 + self.parent.get_depth()


class TaskManager:
    r"""TaskManager is used to manage tasks.

    Attributes:
        root_task: The root task.
        tasks: The ordered tasks.
        task_map: A map for task.id to Task.
        current_task_id: The current "RUNNING" task.id.

    Args:
        task (Task): The root Task.
    """

    def __init__(self, task: Task):
        self.root_task: Task = task
        self.current_task_id: str = task.id
        self.tasks: List[Task] = [task]
        self.task_map: Dict[str, Task] = {task.id: task}

    def gen_task_id(self) -> str:
        r"""Generate a new task id."""
        return f"{len(self.tasks)}"

    def exist(self, task_id: str) -> bool:
        r"""Check if a task with the given id exists."""
        return task_id in self.task_map

    @property
    def current_task(self) -> Optional[Task]:
        r"""Get the current task."""
        return self.task_map.get(self.current_task_id, None)

    @staticmethod
    def topological_sort(tasks: List[Task]) -> List[Task]:
        r"""Sort a list of tasks by topological way.

        Args:
            tasks (List[Task]): The giving list of tasks.

        Returns:
            The sorted list of tasks.
        """
        stack = []
        visited = set()

        # recursive visit the vertices
        def visit(task: Task):
            if task.id in visited:
                return
            visited.add(task.id)

            # go deep for dependencies
            for sub_task in task.subtasks:
                visit(sub_task)

            # add current task to stack which have no dependencies.
            stack.append(task)

        for task in tasks:
            visit(task)

        return stack

    @staticmethod
    def set_tasks_dependence(
        root: Task,
        others: List[Task],
        type: Literal["serial", "parallel"] = "parallel",
    ):
        r"""Set relationship between root task and other tasks.
        Two relationships are currently supported: serial and parallel.
        `serial` :  root -> other1 -> other2
        `parallel`: root -> other1
                         -> other2

        Args:
            root (Task): A root task.
            others (List[Task]): A list of tasks.
        """
        # filter the root task in the others to avoid self-loop dependence.
        others = [other for other in others if other != root]

        if len(others) == 0:
            return
        if type == "parallel":
            for other in others:
                root.add_subtask(other)
        else:
            parent = root
            for child in others:
                parent.add_subtask(child)
                parent = child

    def add_tasks(self, tasks: Union[Task, List[Task]]) -> None:
        r"""self.tasks and self.task_map will be updated by the input tasks."""
        if not tasks:
            return
        if not isinstance(tasks, List):
            tasks = [tasks]
        for task in tasks:
            assert not self.exist(task.id), f"`{task.id}` already existed."
        self.tasks = self.topological_sort(self.tasks + tasks)
        self.task_map = {task.id: task for task in self.tasks}

    def evolve(
        self,
        task: Task,
        agent: ChatAgent,
        template: Optional[TextPrompt] = None,
        task_parser: Optional[Callable[[str, str], List[Task]]] = None,
    ) -> Optional[Task]:
        r"""Evolve a task to a new task.
            Evolve is only used for data generation.
        Args:
            task (Task): A given task.
            agent (ChatAgent): An agent that used to evolve the task.
            template (TextPrompt, optional): A prompt template to evolve task.
                If not provided, the default template will be used.
            task_parser (Callable, optional): A function to extract Task from
                response. If not provided, the default parser will be used.

        Returns:
            Task: The created :obj:`Task` instance or None.
        """

        if template is None:
            template = TASK_EVOLVE_PROMPT

        role_name = agent.role_name
        content = template.format(role_name=role_name, content=task.content)
        msg = BaseMessage.make_user_message(role_name=role_name, content=content)
        response = agent.step(msg)
        if task_parser is None:
            task_parser = parse_response
        tasks = task_parser(response.msg.content, task.id)
        if tasks:
            return tasks[0]
        return None
