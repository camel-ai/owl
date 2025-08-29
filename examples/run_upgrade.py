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
import sys
import pathlib

from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelType
from camel.societies import RolePlaying
from camel.logger import set_log_level

# Assuming the new toolkit is in this path
from owl.utils.system_toolkit import SystemToolkit
from owl.utils import run_society

# Setup environment
base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="INFO")


def construct_society(question: str) -> RolePlaying:
    """
    Constructs a society of agents for the self-upgrade task.
    """
    # Define the model for the agent
    model = ModelFactory.create(
        model_platform="openai",
        model_type=ModelType.GPT_4O,
        model_config_dict={"temperature": 0.2},
    )

    # Instantiate the toolkit
    system_toolkit = SystemToolkit()

    # Get the tool functions from the toolkit instance
    tools = [
        system_toolkit.backup,
        system_toolkit.upgrade,
        system_toolkit.test,
        system_toolkit.restore,
    ]

    # Configure agent roles and parameters
    user_agent_kwargs = {"model": model}
    assistant_agent_kwargs = {"model": model, "tools": tools}

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
    """Main function to run the self-upgrade workflow."""

    # The detailed task prompt that guides the agent
    task_prompt = """
    Your task is to safely upgrade the application's codebase. You must follow these steps precisely:
    1.  First, create a backup of the current application state by calling the `backup` tool.
    2.  After the backup is confirmed, attempt to upgrade the application by calling the `upgrade` tool.
    3.  After the upgrade attempt, you must verify the integrity of the application by calling the `test` tool.
    4.  Analyze the output of the `test` tool. The output will contain the line 'RESULT: Smoke test PASSED.' or 'RESULT: Smoke test FAILED.'.
    5.  If the test passed, your task is complete. Report the success.
    6.  If the test failed, you must restore the application to its previous state by calling the `restore` tool. After restoring, report the failure and the fact that you have restored the backup.
    Do not deviate from this sequence.
    """

    # Construct and run the society
    society = construct_society(task_prompt)
    answer, chat_history, token_count = run_society(society)

    # Output the final result from the agent
    print("\n" + "="*30)
    print("Self-Upgrade Process Final Report:")
    print("="*30)
    print(f"\033[94m{answer}\033[0m")
    print("\nToken usage information:")
    print(token_count)


if __name__ == "__main__":
    main()
