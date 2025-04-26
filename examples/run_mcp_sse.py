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
import asyncio
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.toolkits import FunctionTool
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level
from camel.toolkits import MCPToolkit

from owl.utils.enhanced_role_playing import OwlRolePlaying, arun_society

import pathlib

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")


async def construct_society(
    question: str,
    tools: List[FunctionTool],
) -> OwlRolePlaying:
    r"""Build a multi-agent OwlRolePlaying instance for GitHub information retrieval.

    Args:
        question (str): The GitHub-related question to ask.
        tools (List[FunctionTool]): The MCP tools to use for GitHub interaction.
    """
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        ),
    }

    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {
        "model": models["assistant"],
        "tools": tools,
    }

    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    society = OwlRolePlaying(
        **task_kwargs,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )
    return society


async def main():
    # Load SSE server configuration
    config_path = Path(__file__).parent / "mcp_sse_config.json"
    mcp_toolkit = MCPToolkit(config_path=str(config_path))

    try:
        # Connect to MCP server
        await mcp_toolkit.connect()
        print("Successfully connected to SSE server")

        # Get available tools
        tools = [*mcp_toolkit.get_tools()]

        # Set default task - a simple example query
        default_task = (
            "What are the most recent pull requests in camel-ai/camel repository?"
        )

        # Use command line argument if provided, otherwise use default task
        task = sys.argv[1] if len(sys.argv) > 1 else default_task

        # Build and run society
        society = await construct_society(task, tools)
        answer, chat_history, token_count = await arun_society(society)
        print(f"\nResult: {answer}")

    except KeyboardInterrupt:
        print("\nReceived exit signal, shutting down...")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Ensure safe disconnection
        try:
            await mcp_toolkit.disconnect()
        except Exception as e:
            print(f"Error during disconnect: {e}")


if __name__ == "__main__":
    asyncio.run(main())
