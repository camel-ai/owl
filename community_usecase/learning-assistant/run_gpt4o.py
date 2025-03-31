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
import os
import logging
import json

from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelPlatformType

from camel.toolkits import (
    SearchToolkit,
    BrowserToolkit,
)
from camel.societies import RolePlaying
from camel.logger import set_log_level, get_logger

import pathlib

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")
logger = get_logger(__name__)
file_handler = logging.FileHandler("learning_journey.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

root_logger = logging.getLogger()
root_logger.addHandler(file_handler)


def construct_learning_society(task: str) -> RolePlaying:
    """Construct a society of agents for the learning journey companion.

    Args:
        task (str): The learning task description including what the user wants to learn and what they already know.

    Returns:
        RolePlaying: A configured society of agents for the learning companion.
    """
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.4},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.4},
        ),
        "content_researcher": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.2},
        ),
        "planning": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.3},
        ),
    }

    browser_toolkit = BrowserToolkit(
        headless=False,
        web_agent_model=models["content_researcher"],
        planning_agent_model=models["planning"],
    )

    tools = [
        *browser_toolkit.get_tools(),
        SearchToolkit().search_duckduckgo,
    ]

    user_agent_kwargs = {
        "model": models["user"],
    }

    assistant_agent_kwargs = {
        "model": models["assistant"],
        "tools": tools,
    }

    task_kwargs = {
        "task_prompt": task,
        "with_task_specify": False,
    }

    society = RolePlaying(
        **task_kwargs,
        user_role_name="learner",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="learning_companion",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

    return society


def analyze_chat_history(chat_history):
    """Analyze chat history and extract tool call information."""
    print("\n============ Tool Call Analysis ============")
    logger.info("========== Starting tool call analysis ==========")

    tool_calls = []
    for i, message in enumerate(chat_history):
        if message.get("role") == "assistant" and "tool_calls" in message:
            for tool_call in message.get("tool_calls", []):
                if tool_call.get("type") == "function":
                    function = tool_call.get("function", {})
                    tool_info = {
                        "call_id": tool_call.get("id"),
                        "name": function.get("name"),
                        "arguments": function.get("arguments"),
                        "message_index": i,
                    }
                    tool_calls.append(tool_info)
                    print(
                        f"Tool Call: {function.get('name')} Args: {function.get('arguments')}"
                    )
                    logger.info(
                        f"Tool Call: {function.get('name')} Args: {function.get('arguments')}"
                    )

        elif message.get("role") == "tool" and "tool_call_id" in message:
            for tool_call in tool_calls:
                if tool_call.get("call_id") == message.get("tool_call_id"):
                    result = message.get("content", "")
                    result_summary = (
                        result[:100] + "..." if len(result) > 100 else result
                    )
                    print(
                        f"Tool Result: {tool_call.get('name')} Return: {result_summary}"
                    )
                    logger.info(
                        f"Tool Result: {tool_call.get('name')} Return: {result_summary}"
                    )

    print(f"Total tool calls found: {len(tool_calls)}")
    logger.info(f"Total tool calls found: {len(tool_calls)}")
    logger.info("========== Finished tool call analysis ==========")

    with open("learning_journey_history.json", "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)

    print("Records saved to learning_journey_history.json")
    print("============ Analysis Complete ============\n")


def run_learning_companion(task: str = None):
    """Run the learning companion with the given task.

    Args:
        task (str, optional): The learning task description. Defaults to an example task.
    """
    task = """
    I want to learn about the transformers architecture in an llm.  
    I've also taken a basic statistics course. 
    I have about 10 hours per week to dedicate to learning. Devise a roadmap for me .
    """

    society = construct_learning_society(task)

    from owl.utils import run_society

    answer, chat_history, token_count = run_society(society, round_limit=5)

    # Record tool usage history
    analyze_chat_history(chat_history)
    print(f"\033[94mAnswer: {answer}\033[0m")


if __name__ == "__main__":
    run_learning_companion()
