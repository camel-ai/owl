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
import asyncio
import logging
from collections import deque
from typing import Deque, Dict, List, Optional

from colorama import Fore

from camel.agents import ChatAgent
from camel.configs import ChatGPTConfig
from camel.messages.base import BaseMessage
from camel.models import ModelFactory
from camel.societies.workforce.base import BaseNode
from camel.societies.workforce.prompts import (
    ASSIGN_TASK_PROMPT,
    CREATE_NODE_PROMPT,
    WF_TASK_DECOMPOSE_PROMPT,
    WF_TASK_REPLAN_PROMPT,
)
from camel.societies.workforce.role_playing_worker import RolePlayingWorker
from camel.societies.workforce.single_agent_worker import SingleAgentWorker
from camel.societies.workforce.task_channel import TaskChannel
from camel.societies.workforce.utils import (
    TaskAssignResult,
    WorkerConf,
    check_if_running,
)
from camel.societies.workforce.worker import Worker
from camel.tasks.task import Task, TaskState
from camel.toolkits import GoogleMapsToolkit, SearchToolkit, WeatherToolkit
from camel.types import ModelPlatformType, ModelType

logger = logging.getLogger(__name__)


class Workforce(BaseNode):
    r"""A system where multiple workder nodes (agents) cooperate together
    to solve tasks. It can assign tasks to workder nodes and also take
    strategies such as create new worker, decompose tasks, etc. to handle
    situations when the task fails.

    Args:
        description (str): Description of the node.
        children (Optional[List[BaseNode]], optional): List of child nodes
            under this node. Each child node can be a worker node or
            another workforce node. (default: :obj:`None`)
        coordinator_agent_kwargs (Optional[Dict], optional): Keyword
            arguments for the coordinator agent, e.g. `model`, `api_key`,
            `tools`, etc. (default: :obj:`None`)
        task_agent_kwargs (Optional[Dict], optional): Keyword arguments for
            the task agent, e.g. `model`, `api_key`, `tools`, etc.
            (default: :obj:`None`)
        new_worker_agent_kwargs (Optional[Dict]): Default keyword arguments
            for the worker agent that will be created during runtime to
            handle failed tasks, e.g. `model`, `api_key`, `tools`, etc.
            (default: :obj:`None`)
    """

    def __init__(
        self,
        description: str,
        children: Optional[List[BaseNode]] = None,
        coordinator_agent_kwargs: Optional[Dict] = None,
        task_agent_kwargs: Optional[Dict] = None,
        new_worker_agent_kwargs: Optional[Dict] = None,
    ) -> None:
        super().__init__(description)
        self._child_listening_tasks: Deque[asyncio.Task] = deque()
        self._children = children or []
        self.new_worker_agent_kwargs = new_worker_agent_kwargs

        coord_agent_sys_msg = BaseMessage.make_assistant_message(
            role_name="Workforce Manager",
            content="You are coordinating a group of workers. A worker can be "
            "a group of agents or a single agent. Each worker is "
            "created to solve a specific kind of task. Your job "
            "includes assigning tasks to a existing worker, creating "
            "a new worker for a task, etc.",
        )
        self.coordinator_agent = ChatAgent(coord_agent_sys_msg, **(coordinator_agent_kwargs or {}))

        task_sys_msg = BaseMessage.make_assistant_message(
            role_name="Task Planner",
            content="You are going to compose and decompose tasks.",
        )
        self.task_agent = ChatAgent(task_sys_msg, **(task_agent_kwargs or {}))

        # If there is one, will set by the workforce class wrapping this
        self._task: Optional[Task] = None
        self._pending_tasks: Deque[Task] = deque()

    def __repr__(self):
        return f"Workforce {self.node_id} ({self.description})"

    def _decompose_task(self, task: Task) -> List[Task]:
        r"""Decompose the task into subtasks. This method will also set the
        relationship between the task and its subtasks.

        Returns:
            List[Task]: The subtasks.
        """
        if len(task.failure_info) > 0:
            decompose_prompt = WF_TASK_REPLAN_PROMPT.format(
                content=task.content,
                child_nodes_info=self._get_child_nodes_info(),
                additional_info=task.additional_info,
                failure_info=task.failure_info,
            )
        else:
            decompose_prompt = WF_TASK_DECOMPOSE_PROMPT.format(
                content=task.content,
                child_nodes_info=self._get_child_nodes_info(),
                additional_info=task.additional_info,
            )
        self.task_agent.reset()
        subtasks = task.decompose(self.task_agent, decompose_prompt)
        task.subtasks = subtasks
        for subtask in subtasks:
            subtask.parent = task

        return subtasks

    @check_if_running(False)
    def process_task(self, task: Task) -> Task:
        r"""The main entry point for the workforce to process a task. It will
        start the workforce and all the child nodes under it, process the
        task provided and return the updated task.

        Args:
            task (Task): The task to be processed.

        Returns:
            Task: The updated task.
        """
        self.reset()
        self._task = task
        task.state = TaskState.FAILED
        self._pending_tasks.append(task)
        # The agent tend to be overconfident on the whole task, so we
        # decompose the task into subtasks first
        subtasks = self._decompose_task(task)
        self._pending_tasks.extendleft(reversed(subtasks))
        self.set_channel(TaskChannel())

        asyncio.run(self.start())

        return task

    @check_if_running(False)
    def add_single_agent_worker(self, description: str, worker: ChatAgent) -> Workforce:
        r"""Add a worker node to the workforce that uses a single agent.

        Args:
            description (str): Description of the worker node.
            worker (ChatAgent): The agent to be added.

        Returns:
            Workforce: The workforce node itself.
        """
        worker_node = SingleAgentWorker(description, worker)
        self._children.append(worker_node)
        return self

    @check_if_running(False)
    def add_role_playing_worker(
        self,
        description: str,
        assistant_role_name: str,
        user_role_name: str,
        assistant_agent_kwargs: Optional[Dict] = None,
        user_agent_kwargs: Optional[Dict] = None,
        chat_turn_limit: int = 3,
    ) -> Workforce:
        r"""Add a worker node to the workforce that uses `RolePlaying` system.

        Args:
            description (str): Description of the node.
            assistant_role_name (str): The role name of the assistant agent.
            user_role_name (str): The role name of the user agent.
            assistant_agent_kwargs (Optional[Dict], optional): The keyword
                arguments to initialize the assistant agent in the role
                playing, like the model name, etc. Defaults to `None`.
            user_agent_kwargs (Optional[Dict], optional): The keyword arguments
                to initialize the user agent in the role playing, like the
                model name, etc. Defaults to `None`.
            chat_turn_limit (int, optional): The maximum number of chat turns
                in the role playing. Defaults to 3.

        Returns:
            Workforce: The workforce node itself.
        """
        worker_node = RolePlayingWorker(
            description,
            assistant_role_name,
            user_role_name,
            assistant_agent_kwargs,
            user_agent_kwargs,
            chat_turn_limit,
        )
        self._children.append(worker_node)
        return self

    @check_if_running(False)
    def add_workforce(self, workforce: Workforce) -> Workforce:
        r"""Add a workforce node to the workforce.

        Args:
            workforce (Workforce): The workforce node to be added.

        Returns:
            Workforce: The workforce node itself.
        """
        self._children.append(workforce)
        return self

    @check_if_running(False)
    def reset(self) -> None:
        r"""Reset the workforce and all the child nodes under it. Can only
        be called when the workforce is not running."""
        super().reset()
        self._task = None
        self._pending_tasks.clear()
        self._child_listening_tasks.clear()
        self.coordinator_agent.reset()
        self.task_agent.reset()
        for child in self._children:
            child.reset()

    @check_if_running(False)
    def set_channel(self, channel: TaskChannel) -> None:
        r"""Set the channel for the node and all the child nodes under it."""
        self._channel = channel
        for child in self._children:
            child.set_channel(channel)

    def _get_child_nodes_info(self) -> str:
        r"""Get the information of all the child nodes under this node."""
        info = ""
        for child in self._children:
            if isinstance(child, Workforce):
                additional_info = "A Workforce node"
            elif isinstance(child, SingleAgentWorker):
                additional_info = "tools: " + (", ".join(child.worker.func_dict.keys()))
            elif isinstance(child, RolePlayingWorker):
                additional_info = "A Role playing node"
            else:
                additional_info = "Unknown node"
            info += f"<{child.node_id}>:<{child.description}>:<" f"{additional_info}>\n"
        return info

    def _find_assignee(
        self,
        task: Task,
    ) -> str:
        r"""Assigns a task to a worker node with the best capability.

        Parameters:
            task (Task): The task to be assigned.

        Returns:
            str: ID of the worker node to be assigned.
        """
        self.coordinator_agent.reset()
        prompt = ASSIGN_TASK_PROMPT.format(
            content=task.content,
            child_nodes_info=self._get_child_nodes_info(),
            additional_info=task.additional_info,
        )
        req = BaseMessage.make_user_message(
            role_name="User",
            content=prompt,
        )

        response = self.coordinator_agent.step(req, response_format=TaskAssignResult)
        result_dict = ast.literal_eval(response.msg.content)
        task_assign_result = TaskAssignResult(**result_dict)
        return task_assign_result.assignee_id

    async def _post_task(self, task: Task, assignee_id: str) -> None:
        await self._channel.post_task(task, self.node_id, assignee_id)

    async def _post_dependency(self, dependency: Task) -> None:
        await self._channel.post_dependency(dependency, self.node_id)

    def _create_worker_node_for_task(self, task: Task) -> Worker:
        r"""Creates a new worker node for a given task and add it to the
        children list of this node. This is one of the actions that
        the coordinator can take when a task has failed.

        Args:
            task (Task): The task for which the worker node is created.

        Returns:
            Worker: The created worker node.
        """
        prompt = CREATE_NODE_PROMPT.format(
            content=task.content,
            child_nodes_info=self._get_child_nodes_info(),
            additional_info=task.additional_info,
        )
        req = BaseMessage.make_user_message(
            role_name="User",
            content=prompt,
        )
        response = self.coordinator_agent.step(req, response_format=WorkerConf)
        result_dict = ast.literal_eval(response.msg.content)
        new_node_conf = WorkerConf(**result_dict)

        new_agent = self._create_new_agent(
            new_node_conf.role,
            new_node_conf.sys_msg,
        )

        new_node = SingleAgentWorker(
            description=new_node_conf.description,
            worker=new_agent,
        )
        new_node.set_channel(self._channel)

        print(f"{Fore.CYAN}{new_node} created.{Fore.RESET}")

        self._children.append(new_node)
        self._child_listening_tasks.append(asyncio.create_task(new_node.start()))
        return new_node

    def _create_new_agent(self, role: str, sys_msg: str) -> ChatAgent:
        worker_sys_msg = BaseMessage.make_assistant_message(
            role_name=role,
            content=sys_msg,
        )

        if self.new_worker_agent_kwargs is not None:
            return ChatAgent(worker_sys_msg, **self.new_worker_agent_kwargs)

        # Default tools for a new agent
        function_list = [
            *SearchToolkit().get_tools(),
            *WeatherToolkit().get_tools(),
            *GoogleMapsToolkit().get_tools(),
        ]

        model_config_dict = ChatGPTConfig(
            tools=function_list,
            temperature=0.0,
        ).as_dict()

        model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=ModelType.DEFAULT,
            model_config_dict=model_config_dict,
        )

        return ChatAgent(worker_sys_msg, model=model, tools=function_list)

    async def _get_returned_task(self) -> Task:
        r"""Get the task that's published by this node and just get returned
        from the assignee.
        """
        return await self._channel.get_returned_task_by_publisher(self.node_id)

    async def _post_ready_tasks(self) -> None:
        r"""Send all the pending tasks that have all the dependencies met to
        the channel, or directly return if there is none. For now, we will
        directly send the first task in the pending list because all the tasks
        are linearly dependent."""

        if not self._pending_tasks:
            return

        ready_task = self._pending_tasks[0]

        # If the task has failed previously, just compose and send the task
        # to the channel as a dependency
        if ready_task.state == TaskState.FAILED:
            # TODO: the composing of tasks seems not work very well
            self.task_agent.reset()
            ready_task.compose(self.task_agent)
            # Remove the subtasks from the channel
            for subtask in ready_task.subtasks:
                await self._channel.remove_task(subtask.id)
            # Send the task to the channel as a dependency
            await self._post_dependency(ready_task)
            self._pending_tasks.popleft()
            # Try to send the next task in the pending list
            await self._post_ready_tasks()
        else:
            # Directly post the task to the channel if it's a new one
            # Find a node to assign the task
            assignee_id = self._find_assignee(task=ready_task)
            await self._post_task(ready_task, assignee_id)

    async def _handle_failed_task(self, task: Task) -> bool:
        if task.failure_count >= 3:
            return True
        task.failure_count += 1

        # TODO: if task.failure_reason has content, then replanning, else retry
        if len(task.failure_reason) > 0:
            await self._replan_task(task)

        # TODO: REFINE IT LATER

        # # Remove the failed task from the channel
        # await self._channel.remove_task(task.id)
        # if task.get_depth() >= 3:
        #     # Create a new worker node and reassign
        #     assignee = self._create_worker_node_for_task(task)
        #     await self._post_task(task, assignee.node_id)
        # else:
        #     subtasks = self._decompose_task(task)
        #     # Insert packets at the head of the queue
        #     self._pending_tasks.extendleft(reversed(subtasks))
        #     await self._post_ready_tasks()
        return False

    async def _replan_task(self, failed_task: Task) -> bool:
        from copy import deepcopy

        logger.warning(f"Task {failed_task.id} has failed, replanning the whole task..")

        self._task.failure_info = f"""
            In the previous attempt, when processing a subtask of the current task:
            ```
            {failed_task.content}
            ```
            the above task processing failed for the following reasons (responsed by an agent):
            ```
            {failed_task.failure_reason}
            ```
            When you make a new task division, you need to fully consider the above problems and make corrections.
        """
        overall_task = deepcopy(self._task)
        overall_task.subtasks = []

        self.reset()
        self._task = overall_task
        self._task.state = TaskState.FAILED
        self._pending_tasks.append(overall_task)

        subtasks = self._decompose_task(overall_task)
        self._pending_tasks.extendleft(reversed(subtasks))
        self.set_channel(TaskChannel())

        await self.start()

    async def _handle_completed_task(self, task: Task) -> None:
        # archive the packet, making it into a dependency
        self._pending_tasks.popleft()
        await self._channel.archive_task(task.id)
        await self._post_ready_tasks()

    @check_if_running(False)
    async def _listen_to_channel(self) -> None:
        r"""Continuously listen to the channel, post task to the channel and
        track the status of posted tasks.
        """

        self._running = True
        logger.info(f"Workforce {self.node_id} started.")

        await self._post_ready_tasks()

        while self._task is None or self._pending_tasks:
            returned_task = await self._get_returned_task()
            if returned_task.state == TaskState.DONE:
                await self._handle_completed_task(returned_task)
            elif returned_task.state == TaskState.FAILED:
                halt = await self._handle_failed_task(returned_task)
                if not halt:
                    continue
                print(
                    f"{Fore.RED}Task {returned_task.id} has failed "
                    f"for 3 times, halting the workforce.{Fore.RESET}"
                )
                break
            elif returned_task.state == TaskState.OPEN:
                # TODO: multi-layer workforce
                pass
            else:
                raise ValueError(f"Task {returned_task.id} has an unexpected state.")

        # shut down the whole workforce tree
        self.stop()

    @check_if_running(False)
    async def start(self) -> None:
        r"""Start itself and all the child nodes under it."""
        for child in self._children:
            child_listening_task = asyncio.create_task(child.start())
            self._child_listening_tasks.append(child_listening_task)
        await self._listen_to_channel()

    @check_if_running(True)
    def stop(self) -> None:
        r"""Stop all the child nodes under it. The node itself will be stopped
        by its parent node.
        """
        for child in self._children:
            child.stop()
        for child_task in self._child_listening_tasks:
            child_task.cancel()
        self._running = False
