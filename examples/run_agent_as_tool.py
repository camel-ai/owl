import asyncio
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv
from camel.logger import set_log_level
from camel.models import ModelFactory
from camel.toolkits import (
    CodeExecutionToolkit,
    ImageAnalysisToolkit,
    SearchToolkit,
    BrowserToolkit,
    FileWriteToolkit,
    FunctionTool,
)
from camel.types import ModelPlatformType
from camel.agents import ChatAgent
from owl.utils.enhanced_role_playing import OwlRolePlaying, arun_society

# ----------------------------------------------------------------------------
# 📦 Template: Multi-Agent Role-Playing with CAMEL + OWL (Ollama Edition)
# ----------------------------------------------------------------------------
# - Uses Ollama local models (no API keys required)
# - Demonstrates how to wrap specialized agents as tools
# - Includes stop/continue controls and logging
# - Easily forkable on GitHub

# Set debug logging for CAMEL
set_log_level(level="DEBUG")

# Configure logging for agent-tool calls
logger = logging.getLogger("agent_tools")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("agent_calls.log")
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)

# ==== Control Tools ====
def stop_fn() -> dict:
    logger.info("stop tool invoked")
    return {"action": "stop"}


def continue_fn(steps: int) -> dict:
    logger.info(f"continue tool invoked: steps={steps}")
    return {"action": "continue", "steps": steps}

stop_tool = FunctionTool(stop_fn)
continue_tool = FunctionTool(continue_fn)

# Decorator to set tool metadata
def agent_tool_decorator(role_name: str):
    def decorator(func):
        func.__name__ = f"tool_{role_name}"
        func.__doc__ = (
            f"Delegate to {role_name} agent with step control."
            "\nArgs:\n    prompt(str): user input.\n    steps(int): max iterations.\nReturns:\n    str: agent output."
        )
        return func
    return decorator

# Wrap any ChatAgent as a FunctionTool
def make_agent_tool(role_name: str, agent: ChatAgent) -> FunctionTool:
    @agent_tool_decorator(role_name)
    def tool_func(prompt: str, steps: int = 1) -> str:
        acc = ""
        step = 0
        max_steps = steps
        logger.info(f"{role_name}_start: prompt={prompt}, steps={steps}")
        while step < max_steps:
            res = agent.run(prompt)
            if isinstance(res, dict):
                action = res.get("action")
                if action == "stop": break
                if action == "continue":
                    max_steps += res.get("steps", 0)
                    continue
            acc = res or acc
            logger.info(f"{role_name}_step{step+1}: {acc}")
            if "stop" in (res or "").lower(): break
            step += 1
        return acc

    return FunctionTool(tool_func)

# Construct the society
async def construct_society(prompt: str) -> OwlRolePlaying:
    # 1) Model config: Ollama local
    model_cfg = {
        "model_platform": ModelPlatformType.OLLAMA,
        "model_type": "llama2",  # or your local model name
        "url": None,
        "model_config_dict": {"max_tokens": 2048, "temperature": 0.7},
    }

    # 2) Create models per role
    roles = ["user", "assistant", "browser", "coder", "analyzer"]
    models = {r: ModelFactory.create(**model_cfg) for r in roles}

    # 3) Define specialized agents & their tools
    browser_agent = ChatAgent(
        "You are a web-browsing assistant.",
        model=models["browser"],
        tools=BrowserToolkit(
            headless=True,
            web_agent_model=models["browser"],
            planning_agent_model=models["assistant"],
        ).get_tools() + [stop_tool, continue_tool]
    )

    coder_agent = ChatAgent(
        "You are a code execution assistant.",
        model=models["coder"],
        tools=CodeExecutionToolkit(sandbox="subprocess").get_tools() + [stop_tool, continue_tool]
    )

    analyzer_agent = ChatAgent(
        "You are an image analysis assistant.",
        model=models["analyzer"],
        tools=ImageAnalysisToolkit(model=models["analyzer"]).get_tools() + [stop_tool, continue_tool]
    )

    # 4) Wrap as FunctionTools
    sub_tools = [
        make_agent_tool("browser", browser_agent),
        make_agent_tool("coder", coder_agent),
        make_agent_tool("analyzer", analyzer_agent),
    ]

    # 5) Core assistant gets delegators + search + file write
    assistant_tools = sub_tools + [
        SearchToolkit().search_duckduckgo,
        *FileWriteToolkit(output_dir="./outputs").get_tools(),
        stop_tool,
        continue_tool,
    ]

    # 6) Assemble OwlRolePlaying
    return OwlRolePlaying(
        task_prompt=prompt,
        with_task_specify=False,
        user_role_name="user",
        user_agent_kwargs={"model": models["user"]},
        assistant_role_name="assistant",
        assistant_agent_kwargs={"model": models["assistant"], "tools": assistant_tools},
    )

# Main entrypoint
async def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Start a multi-tool-assisted chat."
    society = await construct_society(prompt)
    answer, history, tokens = await arun_society(society)
    print("Answer:", answer)

if __name__ == "__main__":
    asyncio.run(main())
