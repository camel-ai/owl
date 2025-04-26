import os
import asyncio
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.toolkits import FunctionTool, MCPToolkit
from camel.types import ModelPlatformType, ModelType
from camel.logger import get_logger, set_log_file

from owl.utils.enhanced_role_playing import OwlRolePlaying, arun_society

# Set logging level
set_log_file("notion_mcp.log")
logger = get_logger(__name__)

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../owl/.env'))

async def construct_society(
    question: str,
    tools: List[FunctionTool],
) -> OwlRolePlaying:
    """Build a multi-agent OwlRolePlaying instance for Notion management."""
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={
                "temperature": 0.7,
            },
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={
                "temperature": 0.7,
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
        user_role_name="notion_manager",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="notion_assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

async def execute_notion_task(society: OwlRolePlaying):
    """Execute the Notion task and handle the result."""
    try:
        result = await arun_society(society)
        
        if isinstance(result, tuple) and len(result) == 3:
            answer, chat_history, token_count = result
            logger.info(f"\nTask Result: {answer}")
            logger.info(f"Token count: {token_count}")
        else:
            logger.info(f"\nTask Result: {result}")
            
    except Exception as e:
        logger.info(f"\nError during task execution: {str(e)}")
        raise

async def main():
    config_path = Path(__file__).parent / "mcp_servers_config.json"
    mcp_toolkit = MCPToolkit(config_path=str(config_path))

    try:
        logger.info("Connecting to Notion MCP server...")
        await mcp_toolkit.connect()
        logger.info("Successfully connected to Notion MCP server")

        default_task = (

            "Notion Task:\n"
            "1. Find the page titled 'Travel Itinerary\n"
            "2. Create a list of Top 10 travel destinations in Europe and add them to the page along with their description.\n"
            "3. Also mention the best time to visit these destintions.\n"

        )

        task = sys.argv[1] if len(sys.argv) > 1 else default_task
        logger.info(f"\nExecuting task:\n{task}")

        tools = [*mcp_toolkit.get_tools()]
        society = await construct_society(task, tools)
        
        await execute_notion_task(society)

    except Exception as e:
        logger.info(f"\nError: {str(e)}")
        raise

    finally:
        logger.info("\nPerforming cleanup...")
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        try:
            await mcp_toolkit.disconnect()
            logger.info("Successfully disconnected from Notion MCP server")
        except Exception as e:
            logger.info(f"Cleanup error (can be ignored): {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nReceived keyboard interrupt. Shutting down gracefully...")
    finally:
        if sys.platform == 'win32':
            try:
                import asyncio.windows_events
                asyncio.windows_events._overlapped = None
            except (ImportError, AttributeError):
                pass