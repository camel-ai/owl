from camel.models import ModelFactory
from camel.toolkits import *
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig

from typing import List, Dict
from dotenv import load_dotenv
from retry import retry
from loguru import logger

from utils import OwlRolePlaying, process_tools, run_society
import os


load_dotenv()


def construct_society(question: str) -> OwlRolePlaying:
    r"""Construct the society based on the question."""

    user_role_name = "user"
    assistant_role_name = "assistant"

    user_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O,
        model_config_dict=ChatGPTConfig(temperature=0, top_p=1).as_dict(),  # [Optional] the config for model
    )

    assistant_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O,
        model_config_dict=ChatGPTConfig(temperature=0, top_p=1).as_dict(),  # [Optional] the config for model
    )

    user_tools = []
    assistant_tools = [
        "WebToolkit",
        "DocumentProcessingToolkit",
        "VideoAnalysisToolkit",
        "CodeExecutionToolkit",
        "ImageAnalysisToolkit",
        "AudioAnalysisToolkit",
        "SearchToolkit",
        "ExcelToolkit",
    ]

    user_role_name = "user"
    user_agent_kwargs = {
        "model": user_model,
        "tools": process_tools(user_tools),
    }
    assistant_role_name = "assistant"
    assistant_agent_kwargs = {
        "model": assistant_model,
        "tools": process_tools(assistant_tools),
    }

    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    society = OwlRolePlaying(
        **task_kwargs,
        user_role_name=user_role_name,
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name=assistant_role_name,
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

    return society


# Example case
question = "What was the volume in m^3 of the fish bag that was calculated in the University of Leicester paper `Can Hiccup Supply Enough Fish to Maintain a Dragon’s Diet?` "

society = construct_society(question)
answer, chat_history, token_count = run_society(society)

logger.success(f"Answer: {answer}")
