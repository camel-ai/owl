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
from dotenv import load_dotenv
import os
from camel.models import ModelFactory
from camel.toolkits import (
    SearchToolkit,
    BrowserToolkit,
    FileWriteToolkit,
    TerminalToolkit,
)
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level

from owl.utils import run_society
from camel.societies import RolePlaying

import pathlib

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")


def construct_society(question: str) -> RolePlaying:
    r"""Construct a society of agents based on the given question.

    This function initializes a society of agents with specific roles and tools
    to address the provided task or question. It configures models for different
    components, sets up toolkits, and defines agent roles and task parameters.

    Args:
        question (str): The task or question to be addressed by the society.

    Returns:
        RolePlaying: A configured society of agents ready to address the
            question.
    """

    # Create models for different components of the society
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        ),
        "web": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        ),
        "planning": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        ),
    }

    # Configure toolkits for the assistant agent
    tools = [
        *BrowserToolkit(
            headless=False,  # Set to True for headless mode (e.g., on remote servers)
            web_agent_model=models["web"],
            planning_agent_model=models["planning"],
        ).get_tools(),
        SearchToolkit().search_duckduckgo,
        SearchToolkit().search_wiki,
        *FileWriteToolkit(output_dir="./").get_tools(),
        *TerminalToolkit().get_tools(),
    ]

    # Define keyword arguments for user and assistant agents
    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}

    # Define task-specific parameters
    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    # Create and return the RolePlaying society
    society = RolePlaying(
        **task_kwargs,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

    return society


def main():
    r"""Main function to run the OWL system with an example question.

    This function demonstrates the usage of the `construct_society` function by
    defining an example research question, constructing a society of agents, and
    running the society to obtain results. The results include the answer,
    chat history, and token count, which are printed to the console.
    """

    # Define an example research question
    question = f"""打开百度搜索，总结一下camel-ai的camel框架的github star、fork数目等，并把数字用plot包写成python文件保存到"+{os.path.join
(base_dir, 'final_output')}+"，用本地终端执行python文件显示图出来给我"""

    # Construct and run the society of agents
    society = construct_society(question)
    answer, chat_history, token_count = run_society(society)

    # Print the results
    print(
        f"\033[94mAnswer: {answer}\nChat History: {chat_history}\ntoken_count:{token_count}\033[0m"
    )


if __name__ == "__main__":
    main()
