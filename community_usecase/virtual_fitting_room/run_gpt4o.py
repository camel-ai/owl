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
import functools
import json
from typing import Callable, Any, Dict, List

from dotenv import load_dotenv
from camel.models import ModelFactory, BaseModelBackend

from camel.toolkits import (
    ExcelToolkit,
    ImageAnalysisToolkit,
    SearchToolkit,
    BrowserToolkit,
    FileWriteToolkit,
    VirtualTryOnToolkit
)
from camel.toolkits.base import BaseToolkit
from camel.types import ModelPlatformType

from owl.utils import run_society
from camel.societies import RolePlaying
from camel.logger import set_log_level, get_logger

import pathlib

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

# set detailed log recording for debug
set_log_level(level="DEBUG")
logger = get_logger(__name__)
file_handler = logging.FileHandler('tool_calls.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

root_logger = logging.getLogger()
root_logger.addHandler(file_handler)

def construct_society(question: str) -> RolePlaying:
    r"""Construct a society of agents based on the given question.

    Args:
        question (str): The task or question to be addressed by the society.

    Returns:
        RolePlaying: A configured society of agents ready to address the question.
    """

    # Create models for different components (here I use gpt-4o for all agents, so remember to set the openai key in .env)
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
        "web": ModelFactory.create(
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
        "image": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.4},
        ),
    }

    # prepare toolkits
    image_toolkit = ImageAnalysisToolkit(model=models["image"])
    browser_toolkit = BrowserToolkit(
        headless=False,
        web_agent_model=models["web"],
        planning_agent_model=models["planning"],
    )
    excel_toolkit = ExcelToolkit()
    file_toolkit = FileWriteToolkit(output_dir="./")
    virtual_try_on_toolkit = VirtualTryOnToolkit()
    
    tools = [
        *browser_toolkit.get_tools(),
        *image_toolkit.get_tools(),
        SearchToolkit().search_duckduckgo,
        # SearchToolkit().search_google,
        # SearchToolkit().search_wiki,
        *excel_toolkit.get_tools(),
        *file_toolkit.get_tools(),
        *virtual_try_on_toolkit.get_tools(),
    ]

    # Configure agent roles and parameters
    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}

    # Configure task parameters
    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    # Create and return the society
    society = RolePlaying(
        **task_kwargs,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

    return society


def main():
    r"""Main function to run the OWL system with an example question."""

    question = f"open https://www.uniqlo.com/eu-at/en/women/tops?path=37608%2C84986%2C85018%2C85207 which shows some clothes on sale. First, directly click one image of clothes which should be an big interactive element (don't wrongly click the small like button overlapped on the image!) to go into its specific details page and then get a partial screenshot for this clothes. Second, only after you've get the partial screenshort of the product, using your own virtual try-on toolkit (there is no built-in virtual try-on button on this website, either no third party tool required) to show me the virtual try-on result with the product."

    # Construct and run the society
    society = construct_society(question)
    answer, chat_history, token_count = run_society(society)
    # output the result
    print(f"\033[94mAnswer: {answer}\033[0m")

if __name__ == "__main__":
    main()
