
import asyncio
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.toolkits import FunctionTool
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level
from camel.toolkits import MCPToolkit, SearchToolkit
import sys

from owl.utils.enhanced_role_playing import OwlRolePlaying, arun_society
import logging

logging.basicConfig(level=logging.DEBUG)

# Load environment variables and set logger level
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
load_dotenv()
set_log_level(level="DEBUG")

async def construct_society(task: str, tools: list[FunctionTool]) -> OwlRolePlaying:
    """
    Build a multi-agent OwlRolePlaying instance.
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
    assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}
    task_kwargs = {
        "task_prompt": task,
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

async def run_task(task: str) -> str:
    """
    Connect to MCP servers, run the provided task, and return the answer.
    """
    # Construct the path to your MCP server config file.
    config_path = Path(__file__).parent / "mcp_servers_config.json"
    mcp_toolkit = MCPToolkit(config_path=str(config_path))
    answer = ""
    try:
        logging.debug("Connecting to MCP server...")
        await mcp_toolkit.connect()
        logging.debug("Connected to MCP server.")

        # Prepare all tools from the MCP toolkit and the web search toolkit
        tools = [*mcp_toolkit.get_tools(), SearchToolkit().search_duckduckgo]
        society = await construct_society(task, tools)
        answer, chat_history, token_count = await arun_society(society)
    except Exception as e:
        import traceback
        st.error(f"An error occurred: {e}")
        st.text(traceback.format_exc())
    finally:
        try:
            await mcp_toolkit.disconnect()
        except Exception as e:
            answer += f"\nError during disconnect: {e}"
    return answer

def main():
    st.title("OWL X Puppeteer MCP Server")

    # Get the task from the user
    task = st.text_input("Enter your task",value="Please find the top articles from dev.to this week and go to each article and then summarize it. Please use MCP given to you")

    if st.button("Run Task"):
        if not task.strip():
            st.error("Please enter a valid task.")
        else:
            with st.spinner("Processing the task..."):
                try:
                    # Create a new event loop for the current thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result = new_loop.run_until_complete(run_task(task))
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    result = ""
                finally:
                    new_loop.close()
                st.success("Task completed!")
                st.write(result)

if __name__ == "__main__":
    main()
