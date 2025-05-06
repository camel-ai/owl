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
from camel.configs import MistralConfig
from camel.models import ModelFactory
from camel.toolkits import (
    SearchToolkit,
    BrowserToolkit,
    FileWriteToolkit,
    TerminalToolkit,
    PyAutoGUIToolkit,
    
)
from camel.types import ModelPlatformType, ModelType

from camel.societies import RolePlaying
import os
from camel.logger import get_logger, set_log_file,set_log_level
from owl.utils import run_society, DocumentProcessingToolkit

# Set logging
set_log_file("product.log")
logger = get_logger(__name__)
set_log_level(level="DEBUG")


# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../owl/.env'))
base_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.join(
    os.path.dirname(os.path.dirname(base_dir)), "workspace"
)


def construct_society(question: str) -> RolePlaying:
    r"""Construct a society of agents based on the given question.

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
            model_config_dict=MistralConfig(temperature=0.0).as_dict(),
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_LARGE,
            model_config_dict=MistralConfig(temperature=0.0).as_dict(),
        ),
        "document": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_LARGE,
            model_config_dict=MistralConfig(temperature=0.0).as_dict(),
        ),
        "browsing": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_LARGE,
            model_config_dict=MistralConfig(temperature=0.0).as_dict(),
        ),
        "planning": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_LARGE,
            model_config_dict=MistralConfig(temperature=0.0).as_dict(),
        ),
     

    }

    # Configure toolkits
    tools = [
        *BrowserToolkit(
            headless=False,  # Set to True for headless mode (e.g., on remote servers)
            web_agent_model=models["browsing"],
            planning_agent_model=models["planning"],
        ).get_tools(),
        *PyAutoGUIToolkit().get_tools(),
        *TerminalToolkit(working_dir=workspace_dir).get_tools(),
        # SearchToolkit().search_duckduckgo,
        SearchToolkit().search_google,  # Comment this out if you don't have google search
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
    default_task = """Conduct a comprehensive research on smart city technologies and implementations:

1. Search for the latest smart city initiatives in major global cities and identify common technologies they use.
2. Browse official websites of 2-3 leading smart city technology providers to understand their key solutions.
3. Analyze how IoT sensors, AI, and data analytics are integrated in traffic management and public transportation systems.
4. Research case studies of successful smart city implementations that reduced energy consumption and carbon emissions.
5. Investigate privacy and security concerns in smart city data collection.
6. Create a brief report documenting your findings, including:
   - Top 5 emerging smart city technologies
   - Success metrics used to evaluate smart city projects
   - Implementation challenges and solutions
   - Future trends in smart urban planning
   
Save the report as 'smart_city_research.md' in the current directory with properly formatted sections.
"""

    # Override default task if command line argument is provided
    task = sys.argv[1] if len(sys.argv) > 1 else default_task

    # Construct and run the society
    society = construct_society(task)
    answer, chat_history, token_count = run_society(society)

    # Output the result
    print(f"\033[94mAnswer: {answer}\033[0m")


if __name__ == "__main__":
    main()
