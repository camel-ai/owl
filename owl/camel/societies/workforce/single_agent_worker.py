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

import ast
from typing import Any, List

from colorama import Fore

from camel.agents import ChatAgent
from camel.messages.base import BaseMessage
from camel.societies.workforce.prompts import PROCESS_TASK_PROMPT
from camel.societies.workforce.utils import TaskResult
from camel.societies.workforce.worker import Worker
from camel.tasks.task import Task, TaskState
from camel.utils import print_text_animated


class SingleAgentWorker(Worker):
    r"""A worker node that consists of a single agent.

    Args:
        description (str): Description of the node.
        worker (ChatAgent): Worker of the node. A single agent.
    """

    def __init__(
        self,
        description: str,
        worker: ChatAgent,
    ) -> None:
        super().__init__(description)
        self.worker = worker

    def reset(self) -> Any:
        r"""Resets the worker to its initial state."""
        super().reset()
        self.worker.reset()

    async def _process_task(self, task: Task, dependencies: List[Task]) -> TaskState:
        r"""Processes a task with its dependencies.

        This method asynchronously processes a given task, considering its
        dependencies, by sending a generated prompt to a worker. It updates
        the task's result based on the agent's response.

        Args:
            task (Task): The task to process, which includes necessary details
                like content and type.
            dependencies (List[Task]): Tasks that the given task depends on.

        Returns:
            TaskState: `TaskState.DONE` if processed successfully, otherwise
                `TaskState.FAILED`.
        """
        dependency_tasks_info = self._get_dep_tasks_info(dependencies)
        prompt = PROCESS_TASK_PROMPT.format(
            content=task.content,
            dependency_tasks_info=dependency_tasks_info,
            additional_info=task.additional_info,
        )
        req = BaseMessage.make_user_message(
            role_name="User",
            content=prompt,
        )
        try:
            response = self.worker.step(req, response_format=TaskResult)
        except Exception as e:
            print(f"{Fore.RED}Error occurred while processing task {task.id}:" f"\n{e}{Fore.RESET}")
            return TaskState.FAILED

        print(f"======\n{Fore.GREEN}Reply from {self}:{Fore.RESET}")

        result_dict = ast.literal_eval(response.msg.content)
        task_result = TaskResult(**result_dict)

        color = Fore.RED if task_result.failed else Fore.GREEN
        print_text_animated(
            f"\n{color}{task_result.content}{Fore.RESET}\n======",
            delay=0.005,
        )

        if task_result.failed:
            task.failure_reason = task_result.content
            return TaskState.FAILED

        task.result = task_result.content
        return TaskState.DONE
