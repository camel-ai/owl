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
import json


from camel.models import ModelFactory
from camel.logger import get_logger
from camel.toolkits import (
    # AudioAnalysisToolkit,
    CodeExecutionToolkit,
    ExcelToolkit,
    ImageAnalysisToolkit,
    SearchToolkit,
    # VideoAnalysisToolkit,
    # BrowserToolkit,
    FileWriteToolkit,
)
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig

from owl.utils.gaia import GAIABenchmark
from owl.utils.gaia_multirun import GAIABenchmark as GAIABenchmarkMultirun
from owl.utils.audio_analysis_toolkit import AudioAnalysisToolkit
from owl.utils.browser_toolkit import BrowserToolkit
from owl.utils.video_analysis_toolkit import VideoAnalysisToolkit
from camel.logger import set_log_level

import pathlib

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")

logger = get_logger(__name__)

# Configuration
LEVEL = 'all'
SAVE_RESULT = True

import pandas as pd
df = pd.read_csv('samples_with_index.tsv', sep='\t')
# 获取 task_id 列
task_ids = df['idx']

# test_idx = task_ids.tolist()[0:10]
# import random
# test_idx = random.sample(task_ids.tolist(), 30)

# Optional prompt loading - handle missing file gracefully
# file_path = "./prompt_process/forder_owl_agent_prompt.json"  # Corrected spelling from "promt" to "prompt"
# try:
#     with open(file_path, "r", encoding="utf-8") as f:
#         data_list = json.load(f)
#     print(data_list)
# except FileNotFoundError:
#     logger.warning(f"Prompt file {file_path} not found, using default settings")
#     data_list = []  # Default empty list if file doesn't exist

# USE_SEW_PROMPT = True
# selected_prompt = data_list[2]
# Audio_analysis_prompt = selected_prompt['Audio_analysis_prompt']
# web_agent_system_prompt = selected_prompt['web_agent_system_prompt']
# planning_agent_system_prompt = selected_prompt['planning_agent_system_prompt']
# video_QA_prompt = selected_prompt['video_QA_prompt']


def main():
    """Main function to run the GAIA benchmark."""
    # Create cache directory
    cache_dir = "tmp/"
    os.makedirs(cache_dir, exist_ok=True)
    result_dir = "results/"
    os.makedirs(result_dir, exist_ok=True)

    # Create models for different components
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=ChatGPTConfig(temperature=0, top_p=1).as_dict(),
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=ChatGPTConfig(temperature=0, top_p=1).as_dict(),
        ),
        "browsing": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=ChatGPTConfig(temperature=0, top_p=1).as_dict(),
        ),
        "planning": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=ChatGPTConfig(temperature=0, top_p=1).as_dict(),
        ),
        "video": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=ChatGPTConfig(temperature=0, top_p=1).as_dict(),
        ),
        "image": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=ChatGPTConfig(temperature=0, top_p=1).as_dict(),
        ),
    }

    # Configure toolkits
    tools = [
        *BrowserToolkit(
            headless=False,  # Set to True for headless mode (e.g., on remote servers)
            web_agent_model=models["browsing"],
            planning_agent_model=models["planning"],
        ).get_tools(),
        *VideoAnalysisToolkit(
            model=models["video"]
        ).get_tools(),  # This requires OpenAI Key
        *AudioAnalysisToolkit().get_tools(),  # This requires OpenAI Key
        *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
        *ImageAnalysisToolkit(model=models["image"]).get_tools(),
        *SearchToolkit().get_tools(),
        *ExcelToolkit().get_tools(),
        *FileWriteToolkit(output_dir="./").get_tools(),
    ]

    # Configure agent roles and parameters
    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}

    # Initialize benchmark
    SUFFIX = "_allvalid_SEW_forder_index11.json"
    # SUFFIX = "_random30.json"
    save_dir = "results"
    os.makedirs(save_dir, exist_ok=True)
    benchmark = GAIABenchmarkMultirun(data_dir="data/gaia", save_to=os.path.join(save_dir, SUFFIX), processes=10)

    # Print benchmark information
    print(f"Number of validation examples: {len(benchmark.valid)}")
    print(f"Number of test examples: {len(benchmark.test)}")

    # Run benchmark
    result = benchmark.run(
        on="valid",
        level=LEVEL,
        # idx=test_idx,
        save_result=SAVE_RESULT,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

    # Output results
    logger.info(f"Correct: {result['correct']}, Total: {result['total']}")
    logger.info(f"Accuracy: {result['accuracy']}")


if __name__ == "__main__":
    main()
