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

from camel.models import ModelFactory
from camel.toolkits import (
    ExcelToolkit,
    SearchToolkit,
    FileWriteToolkit,
    CodeExecutionToolkit,
    BrowserToolkit,
    VideoAnalysisToolkit,
    ImageAnalysisToolkit,
)
from camel.types import ModelPlatformType, ModelType
from camel.societies import RolePlaying
from camel.logger import set_log_level

from owl.utils import run_society, DocumentProcessingToolkit

import pathlib

# Set the log level to DEBUG for detailed debugging information
set_log_level(level="DEBUG")

# Get the parent directory of the current file and construct the path to the .env file
base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))


def get_user_input(prompt):
    # Get user input and strip leading/trailing whitespace
    return input(prompt).strip()


def get_construct_params() -> dict[str, any]:
    # Welcome message
    print("Welcome to owl! Have fun!")

    # Select model platform type
    model_platforms = ModelPlatformType
    print("Please select the model platform type:")
    for i, platform in enumerate(model_platforms, 1):
        print(f"{i}. {platform}")
    model_platform_choice = int(
        get_user_input("Please enter the model platform number:")
    )
    selected_model_platform = list(model_platforms)[model_platform_choice - 1]
    print(f"The model platform you selected is: {selected_model_platform}")

    # Select model type
    models = ModelType
    print("Please select the model type:")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model}")
    model_choice = int(get_user_input("Please enter the model number:"))
    selected_model = list(models)[model_choice - 1]
    print(f"The model you selected is: {selected_model}")

    # Select language
    languages = ["English", "Chinese"]
    print("Please select the language:")
    for i, lang in enumerate(languages, 1):
        print(f"{i}. {lang}")
    language_choice = int(get_user_input("Please enter the language number:"))
    selected_language = languages[language_choice - 1]
    print(f"The language you selected is: {selected_language}")

    # Enter the question
    question = get_user_input("Please enter your question:")
    print(f"Your question is: {question}")

    return {
        "language": selected_language,
        "model_type": selected_model,
        "model_platform": selected_model_platform,
        "question": question,
    }


def construct_society() -> RolePlaying:
    # Get user input parameters
    params = get_construct_params()
    question = params["question"]
    selected_model_type = params["model_type"]
    selected_model_platform = params["model_platform"]
    selected_language = params["language"]

    # Create model instances for different roles
    models = {
        "user": ModelFactory.create(
            model_platform=selected_model_platform,
            model_type=selected_model_type,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=selected_model_platform,
            model_type=selected_model_type,
            model_config_dict={"temperature": 0},
        ),
        "browsing": ModelFactory.create(
            model_platform=selected_model_platform,
            model_type=selected_model_type,
            model_config_dict={"temperature": 0},
        ),
        "planning": ModelFactory.create(
            model_platform=selected_model_platform,
            model_type=selected_model_type,
            model_config_dict={"temperature": 0},
        ),
        "video": ModelFactory.create(
            model_platform=selected_model_platform,
            model_type=selected_model_type,
            model_config_dict={"temperature": 0},
        ),
        "image": ModelFactory.create(
            model_platform=selected_model_platform,
            model_type=selected_model_type,
            model_config_dict={"temperature": 0},
        ),
        "document": ModelFactory.create(
            model_platform=selected_model_platform,
            model_type=selected_model_type,
            model_config_dict={"temperature": 0},
        ),
    }

    # Configure toolkits
    tools = [
        *BrowserToolkit(
            headless=False,
            web_agent_model=models["browsing"],
            planning_agent_model=models["planning"],
        ).get_tools(),
        *VideoAnalysisToolkit(model=models["video"]).get_tools(),
        *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
        *ImageAnalysisToolkit(model=models["image"]).get_tools(),
        SearchToolkit().search_duckduckgo,
        SearchToolkit().search_google,
        SearchToolkit().search_wiki,
        SearchToolkit().search_baidu,
        SearchToolkit().search_bing,
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
        output_language=selected_language,
    )

    return society


def main():
    # Construct the society
    society = construct_society()
    # Run the society and get the answer, chat history, and token count
    answer, chat_history, token_count = run_society(society)
    # Print the answer
    print(f"\033[94mAnswer: {answer}\033[0m")


if __name__ == "__main__":
    main()
