import asyncio
import sys
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.toolkits import FunctionTool, MCPToolkit
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level

from owl.utils.enhanced_role_playing import OwlRolePlaying, arun_society

import pathlib

set_log_level(level="DEBUG")

# Load environment variables from .env file if available
load_dotenv()


async def construct_society(
    question: str,
    tools: List[FunctionTool],
) -> OwlRolePlaying:
    """Build a multi-agent OwlRolePlaying instance with enhanced content curation capabilities."""
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={
                "temperature": 0.7,
                # "max_tokens": 4000  # Add token limit to prevent overflow
            },
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={
                "temperature": 0.7,
                #"max_tokens": 4000
            },
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

    return OwlRolePlaying(
        **task_kwargs,
        user_role_name="content_curator",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="research_assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

async def main():
    config_path = Path(__file__).parent / "mcp_servers_config.json"
    mcp_toolkit = MCPToolkit(config_path=str(config_path))

    try:
        await mcp_toolkit.connect()

        default_task = (
            "Find me the best Airbnb in Gurugram with a check-in date of 2025-06-01 "
            "and a check-out date of 2025-06-07 for 2 adults. Return the top 5 listings with their names, "
            "prices, and locations."
        )

        task = sys.argv[1] if len(sys.argv) > 1 else default_task

        # Connect to all MCP toolkits
        tools = [*mcp_toolkit.get_tools()]
        society = await construct_society(task, tools)
        
        try:
            # Add error handling for the society execution
            result = await arun_society(society)
            
            # Handle the result properly
            if isinstance(result, tuple) and len(result) == 3:
                answer, chat_history, token_count = result
            else:
                answer = str(result)
                chat_history = []
                token_count = 0

        except Exception as e:
            print(f"Error during society execution: {str(e)}")
            raise

    finally:
        # Cleanup
        await asyncio.sleep(1)
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        try:
            await mcp_toolkit.disconnect()
        except Exception as e:
            print(f"Cleanup error (can be ignored): {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    finally:
        if sys.platform == 'win32':
            try:
                import asyncio.windows_events
                asyncio.windows_events._overlapped = None
            except (ImportError, AttributeError):
                pass