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
"""MCP Multi-Agent System Example

This example demonstrates how to use MCP (Model Context Protocol) with CAMEL agents
for advanced information retrieval and processing tasks.

Environment Setup:
1. Configure the required dependencies of owl library
   Refer to: https://github.com/camel-ai/owl for installation guide

2. MCP Server Setup:


   2.1 MCP Playwright Service:
   ```bash
   # Install MCP service
   npm install -g @executeautomation/playwright-mcp-server
   npx playwright install-deps

   # Configure in mcp_servers_config.json:
   {
     "mcpServers": {
       "playwright": {
         "command": "npx",
         "args": ["-y", "@executeautomation/playwright-mcp-server"]
       }
     }
   }
   ```

   2.2 MCP Fetch Service (Optional - for better retrieval):
   ```bash
   # Install MCP service
   pip install mcp-server-fetch

   # Configure in mcp_servers_config.json:
   {
     "mcpServers": {
       "fetch": {
         "command": "python",
         "args": ["-m", "mcp_server_fetch"]
       }
     }
   }
   ```

Usage:
1. Ensure all MCP servers are properly configured in mcp_servers_config.json
2. Run this script to create a multi-agent system that can:
   - Access and manipulate files through MCP Desktop Commander
   - Perform web automation tasks using Playwright
   - Process and generate information using Mistral
   - Fetch web content (if fetch service is configured)
3. The system will execute the specified task while maintaining security through
   controlled access

Note:
- All file operations are restricted to configured directories
- Supports asynchronous operations for efficient processing
"""

import asyncio
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.toolkits import FunctionTool
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level
from camel.toolkits import MCPToolkit, FileWriteToolkit, CodeExecutionToolkit
from camel.societies import RolePlaying

from owl.utils.enhanced_role_playing import arun_society

import pathlib

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")


async def construct_society(
    question: str,
    tools: List[FunctionTool],
) -> RolePlaying:
    r"""build a multi-agent RolePlaying instance.

    Args:
        question (str): The question to ask.
        tools (List[FunctionTool]): The MCP tools to use.
    """
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_MEDIUM_3,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.MISTRAL,
            model_type=ModelType.MISTRAL_LARGE,
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

    society = RolePlaying(
        **task_kwargs,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )
    return society


async def main():
    config_path = Path(__file__).parent / "mcp_servers_config.json"
    mcp_toolkit = MCPToolkit(config_path=str(config_path))

    try:
        await mcp_toolkit.connect()

        # Default task
        default_task = (
            "Help me search the latest reports about smart city, "
            "summarize them and help me generate a PDF file. You have "
            "been provided with tools to do browser operation. Open "
            "browser to finish the task."
        )

        # Override default task if command line argument is provided
        task = sys.argv[1] if len(sys.argv) > 1 else default_task

        # Connect to toolkits
        tools = [
            *mcp_toolkit.get_tools(),
            *FileWriteToolkit().get_tools(),
            *CodeExecutionToolkit().get_tools(),
        ]
        society = await construct_society(task, tools)
        answer, chat_history, token_count = await arun_society(society)
        print(f"\033[94mAnswer: {answer}\033[0m")

    finally:
        # Make sure to disconnect safely after all operations are completed.
        try:
            await mcp_toolkit.disconnect()
        except Exception:
            print("Disconnect failed")


if __name__ == "__main__":
    asyncio.run(main())
