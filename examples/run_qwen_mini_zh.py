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

# To run this file, you need to configure the Qwen API key
# You can obtain your API key from Bailian platform: bailian.console.aliyun.com
# Set it as QWEN_API_KEY="your-api-key" in your .env file or add it to your environment variables

from dotenv import load_dotenv
import sys
from camel.models import ModelFactory
from camel.toolkits import BrowserToolkit, SearchToolkit, FileWriteToolkit
from camel.types import ModelPlatformType, ModelType

from owl.utils import run_society

from camel.societies import RolePlaying

from camel.logger import set_log_level

import pathlib

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")


def construct_society(question: str) -> RolePlaying:
    r"""Construct the society based on the question."""

    user_role_name = "user"
    assistant_role_name = "assistant"

    user_model = ModelFactory.create(
        model_platform=ModelPlatformType.QWEN,
        model_type=ModelType.QWEN_MAX,
        model_config_dict={"temperature": 0},
    )

    assistant_model = ModelFactory.create(
        model_platform=ModelPlatformType.QWEN,
        model_type=ModelType.QWEN_MAX,
        model_config_dict={"temperature": 0},
    )

    planning_model = ModelFactory.create(
        model_platform=ModelPlatformType.QWEN,
        model_type=ModelType.QWEN_MAX,
        model_config_dict={"temperature": 0},
    )

    web_model = ModelFactory.create(
        model_platform=ModelPlatformType.QWEN,
        model_type=ModelType.QWEN_VL_MAX,
        model_config_dict={"temperature": 0},
    )

    tools_list = [
        *BrowserToolkit(
            headless=False,
            web_agent_model=web_model,
            planning_agent_model=planning_model,
            output_language="Chinese",
        ).get_tools(),
        SearchToolkit().search_baidu,
        *FileWriteToolkit(output_dir="./").get_tools(),
    ]

    user_role_name = "user"
    user_agent_kwargs = dict(model=user_model)
    assistant_role_name = "assistant"
    assistant_agent_kwargs = dict(model=assistant_model, tools=tools_list)

    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    society = RolePlaying(
        **task_kwargs,
        user_role_name=user_role_name,
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name=assistant_role_name,
        assistant_agent_kwargs=assistant_agent_kwargs,
        output_language="Chinese",
    )

    return society


# Example case
default_task = "浏览亚马逊并找出一款对程序员有吸引力的产品。请提供产品名称和价格"

# Override default task if command line argument is provided
task = sys.argv[1] if len(sys.argv) > 1 else default_task

# Construct and run the society
society = construct_society(task)

answer, chat_history, token_count = run_society(society)

print(f"\033[94mAnswer: {answer}\033[0m")
