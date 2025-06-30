# Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved.
# Licensed under the Apache License, Version 2.0

import sys
from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.toolkits import (
    CodeExecutionToolkit,
    ExcelToolkit,
    ImageAnalysisToolkit,
    SearchToolkit,
    BrowserToolkit,
    FileWriteToolkit,
)
from camel.types import ModelPlatformType
from owl.utils import run_society
from camel.societies import RolePlaying
from camel.logger import set_log_level
import pathlib

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")

def construct_society(question: str) -> RolePlaying:
    # Create models for different components
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OLLAMA,
            model_type="mistral",
            url="http://localhost:11434/v1",
            model_config_dict={"temperature": 0.8, "max_tokens": 1000000},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OLLAMA,
            model_type="mistral",
            url="http://localhost:11434/v1",
            model_config_dict={"temperature": 0.2, "max_tokens": 1000000},
        ),
        "browsing": ModelFactory.create(
            model_platform=ModelPlatformType.OLLAMA,
            model_type="llava",
            url="http://localhost:11434/v1",
            model_config_dict={"temperature": 0.4, "max_tokens": 1000000},
        ),
        "planning": ModelFactory.create(
            model_platform=ModelPlatformType.OLLAMA,
            model_type="mistral",
            url="http://localhost:11434/v1",
            model_config_dict={"temperature": 0.4, "max_tokens": 1000000},
        ),
        "image": ModelFactory.create(
            model_platform=ModelPlatformType.OLLAMA,
            model_type="llava",
            url="http://localhost:11434/v1",
            model_config_dict={"temperature": 0.4, "max_tokens": 1000000},
        ),
    }

    # Configure toolkits
    tools = [
        *BrowserToolkit(
            headless=False,
            web_agent_model=models["browsing"],
            planning_agent_model=models["planning"],
        ).get_tools(),
        *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
        *ImageAnalysisToolkit(model=models["image"]).get_tools(),
        SearchToolkit().search_duckduckgo,
        SearchToolkit().search_wiki,
        *ExcelToolkit().get_tools(),
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
    default_task = "Open Brave search, summarize the github stars, fork counts, etc. of camel-ai's camel framework, and write the numbers into a python file using the plot package, save it locally, and run the generated python file."
    task = sys.argv[1] if len(sys.argv) > 1 else default_task
    society = construct_society(task)
    answer, chat_history, token_count = run_society(society)
    print(f"\033[94mAnswer: {answer}\033[0m")

if __name__ == "__main__":
    main()
