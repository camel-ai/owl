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
from typing import Dict, List, Optional

from colorama import Fore

from camel.agents.chat_agent import ChatAgent
from camel.messages.base import BaseMessage
from camel.societies import RolePlaying
from camel.societies.workforce.prompts import (
    ROLEPLAY_PROCESS_TASK_PROMPT,
    ROLEPLAY_SUMMARIZE_PROMPT,
)
from camel.societies.workforce.utils import TaskResult
from camel.societies.workforce.worker import Worker
from camel.tasks.task import Task, TaskState
from camel.utils import print_text_animated


class RolePlayingWorker(Worker):
    r"""A worker node that contains a role playing.

    Args:
        description (str): Description of the node.
        assistant_role_name (str): The role name of the assistant agent.
        user_role_name (str): The role name of the user agent.
        assistant_agent_kwargs (Optional[Dict], optional): The keyword
            arguments to initialize the assistant agent in the role playing,
            like the model name, etc. Defaults to None.
        user_agent_kwargs (Optional[Dict], optional): The keyword arguments to
            initialize the user agent in the role playing, like the model name,
            etc. Defaults to None.
        chat_turn_limit (int, optional): The maximum number of chat turns in
            the role playing. Defaults to 3.
    """

    def __init__(
        self,
        description: str,
        assistant_role_name: str,
        user_role_name: str,
        assistant_agent_kwargs: Optional[Dict] = None,
        user_agent_kwargs: Optional[Dict] = None,
        chat_turn_limit: int = 3,
    ) -> None:
        super().__init__(description)
        summ_sys_msg = BaseMessage.make_assistant_message(
            role_name="Summarizer",
            content="You are a good summarizer. You will be presented with "
            "scenarios where an assistant and a user with specific roles "
            "are trying to solve a task. Your job is summarizing the result "
            "of the task based on the chat history.",
        )
        self.summarize_agent = ChatAgent(summ_sys_msg)
        self.chat_turn_limit = chat_turn_limit
        self.assistant_role_name = assistant_role_name
        self.user_role_name = user_role_name
        self.assistant_agent_kwargs = assistant_agent_kwargs
        self.user_agent_kwargs = user_agent_kwargs
        self.chat_history = []

    async def _process_task(self, task: Task, dependencies: List[Task]) -> TaskState:
        r"""Processes a task leveraging its dependencies through role-playing.

        This method orchestrates a role-playing session between an AI
        assistant and an AI user to process a given task. It initiates with a
        generated prompt based on the task and its dependencies, conducts a
        dialogue up to a specified chat turn limit, and then summarizes the
        dialogue to determine the task's outcome.

        Args:
            task (Task): The task object to be processed, containing necessary
                details like content and type.
            dependencies (List[Task]): A list of task objects that the current
                task depends on.

        Returns:
            TaskState: `TaskState.DONE` if processed successfully, otherwise
                `TaskState.FAILED`.
        """
        dependency_tasks_info = self._get_dep_tasks_info(dependencies)
        prompt = ROLEPLAY_PROCESS_TASK_PROMPT.format(
            content=task.content,
            dependency_task_info=dependency_tasks_info,
            additional_info=task.additional_info,
        )
        role_play_session = RolePlaying(
            assistant_role_name=self.assistant_role_name,
            user_role_name=self.user_role_name,
            assistant_agent_kwargs=self.assistant_agent_kwargs,
            user_agent_kwargs=self.user_agent_kwargs,
            task_prompt=prompt,
            with_task_specify=False,
        )
        n = 0
        input_msg = role_play_session.init_chat()
        chat_history = []
        while n < self.chat_turn_limit:
            n += 1
            assistant_response, user_response = role_play_session.step(input_msg)

            if assistant_response.terminated:
                reason = assistant_response.info["termination_reasons"]
                print(f"{Fore.GREEN}AI Assistant terminated. Reason: " f"{reason}.{Fore.RESET}")
                break

            if user_response.terminated:
                reason = user_response.info["termination_reasons"]
                print(f"{Fore.GREEN}AI User terminated. Reason: {reason}." f"{Fore.RESET}")
                break

            print_text_animated(
                f"{Fore.BLUE}AI User:\n\n{user_response.msg.content}" f"{Fore.RESET}\n",
                delay=0.005,
            )
            chat_history.append(f"AI User: {user_response.msg.content}")

            print_text_animated(f"{Fore.GREEN}AI Assistant:{Fore.RESET}", delay=0.005)

            for func_record in assistant_response.info["tool_calls"]:
                print(func_record)

            print_text_animated(
                f"\n{Fore.GREEN}{assistant_response.msg.content}" f"{Fore.RESET}\n",
                delay=0.005,
            )
            chat_history.append(f"AI Assistant: {assistant_response.msg.content}")

            if "CAMEL_TASK_DONE" in user_response.msg.content:
                break

            input_msg = assistant_response.msg

        chat_history_str = "\n".join(chat_history)
        prompt = ROLEPLAY_SUMMARIZE_PROMPT.format(
            user_role=self.user_role_name,
            assistant_role=self.assistant_role_name,
            content=task.content,
            chat_history=chat_history_str,
            additional_info=task.additional_info,
        )
        req = BaseMessage.make_user_message(
            role_name="User",
            content=prompt,
        )
        response = self.summarize_agent.step(req, response_format=TaskResult)
        result_dict = ast.literal_eval(response.msg.content)
        task_result = TaskResult(**result_dict)
        task.result = task_result.content
        self.chat_history = chat_history

        print(f"Task result: {task.result}\n")
        return TaskState.DONE
