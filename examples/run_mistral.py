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
import sys
import pathlib
from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.toolkits import (
    AudioAnalysisToolkit,
    CodeExecutionToolkit,
    ExcelToolkit,
    ImageAnalysisToolkit,
    SearchToolkit,
    VideoAnalysisToolkit,
    BrowserToolkit,
    FileWriteToolkit,
)
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level
from camel.societies import RolePlaying

from owl.utils import run_society, DocumentProcessingToolkit

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")


def construct_society(question: str) -> RolePlaying:
    r"""Construct a society of agents based on Mistral model(s).

    Args:
        question (str): The task or question to be addressed by the society.

    Returns:
        RolePlaying: A configured society of agents ready to address the question.
    """

    # Create models for different components
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_LARGE,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_LARGE,
            model_config_dict={"temperature": 0},
        ),
        "browsing": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_LARGE,
            model_config_dict={"temperature": 0},
        ),
        "planning": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_LARGE,
            model_config_dict={"temperature": 0},
        ),
        "video": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_PIXTRAL_12B,
            model_config_dict={"temperature": 0},
        ),
        "image": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_PIXTRAL_12B,
            model_config_dict={"temperature": 0},
        ),
        "document": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_LARGE,
            model_config_dict={"temperature": 0},
        ),
    }

    # Configure toolkits
    tools = [
        *BrowserToolkit(
            headless=True,
            web_agent_model=models["browsing"],
            planning_agent_model=models["planning"],
        ).get_tools(),
        *VideoAnalysisToolkit(model=models["video"]).get_tools(),
        *AudioAnalysisToolkit().get_tools(),
        *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
        *ImageAnalysisToolkit(model=models["image"]).get_tools(),
        SearchToolkit().search_duckduckgo,
        SearchToolkit().search_google,
        SearchToolkit().search_wiki,
        *ExcelToolkit().get_tools(),
        *DocumentProcessingToolkit(model=models["document"]).get_tools(),
        *FileWriteToolkit(output_dir="./").get_tools(),
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
    # Default research question
    default_task = "Navigate to Amazon.com and identify one product that is attractive to coders. Please provide me with the product name and price. No need to verify your answer."

    # Override default task if command line argument is provided
    task = sys.argv[1] if len(sys.argv) > 1 else default_task

    # Construct and run the society
    society = construct_society(task)
    answer, chat_history, token_count = run_society(society)

    # Output the result
    print(f"\033[94mAnswer: {answer}\033[0m")


if __name__ == "__main__":
    main()
