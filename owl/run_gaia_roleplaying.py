from camel.models import ModelFactory
from camel.toolkits import *
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig
from utils import GAIABenchmark, process_tools

from dotenv import load_dotenv
from retry import retry
from loguru import logger

import os
import shutil

load_dotenv()


LEVEL = 1
SAVE_RESULT = True
test_idx = [0]


def main():

    cache_dir = "tmp/"
    os.makedirs(cache_dir, exist_ok=True)

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

    benchmark = GAIABenchmark(data_dir="data/gaia", save_to=f"results/result.json")

    print(f"Number of validation examples: {len(benchmark.valid)}")
    print(f"Number of test examples: {len(benchmark.test)}")

    result = benchmark.run(
        on="valid",
        level=LEVEL,
        idx=test_idx,
        save_result=SAVE_RESULT,
        user_role_name=user_role_name,
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name=assistant_role_name,
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

    logger.success(f"Correct: {result['correct']}, Total: {result['total']}")
    logger.success(f"Accuracy: {result['accuracy']}")


if __name__ == "__main__":
    main()
