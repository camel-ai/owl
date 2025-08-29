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
import time
import pathlib
from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelType
from camel.societies import RolePlaying
from camel.logger import set_log_level

from owl.utils.developer_toolkit import DeveloperToolkit
from owl.utils import run_society

# Setup environment
base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="INFO")


def construct_society(question: str) -> RolePlaying:
    """
    Constructs a society of agents for the developer daemon task.
    """
    model = ModelFactory.create(
        model_platform="openai",
        model_type=ModelType.GPT_4O,
        model_config_dict={"temperature": 0.2},
    )

    developer_toolkit = DeveloperToolkit()
    tools = [
        developer_toolkit.list_files,
        developer_toolkit.read_file,
        developer_toolkit.write_file,
        developer_toolkit.check_for_git_updates,
        developer_toolkit.run_tests,
        developer_toolkit.run_upgrade_from_git,
    ]

    assistant_agent_kwargs = {"model": model, "tools": tools}
    user_agent_kwargs = {"model": model}

    return RolePlaying(
        task_prompt=question,
        user_role_name="user",
        assistant_role_name="assistant",
        user_agent_kwargs=user_agent_kwargs,
        assistant_agent_kwargs=assistant_agent_kwargs,
    )


def main():
    """Main function to run the developer daemon."""
    print("Starting Daemon Developer Agent...")
    print("This agent will run in a continuous loop to improve the codebase.")

    # This backlog can be expanded with more development tasks.
    development_backlog = [
        "1. Add a new function to the `CSVToolkit` in `owl/utils/csv_toolkit.py` called `get_row_count` that reads a CSV and returns the number of rows (excluding the header).",
        "2. Refactor the `SystemToolkit` to use the new `DeveloperToolkit`'s `_run_command` helper to reduce code duplication.",
        # Add more tasks here in the future.
    ]

    while True:
        print("\n" + "="*50)
        print("Starting new development cycle...")
        print("="*50)

        task_prompt = f"""
        Your goal is to continuously improve this application. Your workflow for this cycle is as follows:

        1.  **Check for External Updates:** First, call the `check_for_git_updates` tool to see if there are any new commits in the main repository.

        2.  **Apply External Updates (if any):** If updates are available, call the `run_upgrade_from_git` tool to safely apply them. This tool handles backup, upgrade, testing, and restore automatically. Report the result of this process and your cycle is complete.

        3.  **Work on Internal Tasks (if no external updates):** If no external updates are found, you must work on an internal development task. Here is the current backlog of tasks:
            ---
            {chr(10).join(development_backlog)}
            ---
            Choose the *first* task from this list that has not been completed.

        4.  **Implement the Internal Task:**
            a. Use your `list_files` and `read_file` tools to understand the current codebase related to the task.
            b. Plan the necessary code changes.
            c. Use the `write_file` tool to implement the changes.
            d. After writing the code, use the `run_tests` tool to ensure you haven't broken anything.
            e. Report a summary of the changes you made and the result of the tests. Your cycle is then complete.
        """

        # Construct and run the society for one cycle
        society = construct_society(task_prompt)
        answer, _, _ = run_society(society)

        print("\n" + "-"*50)
        print("Development Cycle Complete. Final Report from Agent:")
        print(f"\033[94m{answer}\033[0m")
        print("-" * 50)

        # Wait for a few seconds before starting the next cycle
        print("\nWaiting for 10 seconds before next cycle...")
        time.sleep(10)


if __name__ == "__main__":
    main()
