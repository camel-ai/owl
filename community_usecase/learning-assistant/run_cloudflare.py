#!/usr/bin/env python3
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
import logging
import json

from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelPlatformType

from camel.toolkits import (
    SearchToolkit,
    BrowserToolkit,
)
from camel.societies import RolePlaying
from camel.logger import set_log_level, get_logger

import pathlib

base_dir = pathlib.Path(__file__).parent.parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")
logger = get_logger(__name__)
file_handler = logging.FileHandler("learning_journey.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

root_logger = logging.getLogger()
root_logger.addHandler(file_handler)

# Cloudflare configuration
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
MODEL_TYPE = os.getenv("MODEL_TYPE", "@cf/meta/llama-4-scout-17b-16e-instruct")

def construct_learning_society(task: str) -> RolePlaying:
    """Construct a society of agents for the learning journey companion using Cloudflare Workers AI.

    Args:
        task (str): The learning task description including what the user wants to learn and what they already know.

    Returns:
        RolePlaying: A configured society of agents for the learning companion.
    """
    
    # Check if Cloudflare credentials are available
    if not CF_API_TOKEN or not CF_ACCOUNT_ID:
        logger.error("CF_API_TOKEN and CF_ACCOUNT_ID must be set for Cloudflare Workers AI")
        raise ValueError("Cloudflare credentials not found. Please set CF_API_TOKEN and CF_ACCOUNT_ID environment variables.")
    
    # Create Cloudflare Workers AI models
    gateway_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1"
    
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=MODEL_TYPE,
            api_key=CF_API_TOKEN,
            url=gateway_url,
            model_config_dict={"temperature": 0.4, "max_tokens": 32000},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=MODEL_TYPE,
            api_key=CF_API_TOKEN,
            url=gateway_url,
            model_config_dict={"temperature": 0.4, "max_tokens": 32000},
        ),
        "content_researcher": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=MODEL_TYPE,
            api_key=CF_API_TOKEN,
            url=gateway_url,
            model_config_dict={"temperature": 0.2, "max_tokens": 32000},
        ),
        "planning": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=MODEL_TYPE,
            api_key=CF_API_TOKEN,
            url=gateway_url,
            model_config_dict={"temperature": 0.3, "max_tokens": 32000},
        ),
    }

    logger.info(f"Using Cloudflare Workers AI model: {MODEL_TYPE}")
    logger.info(f"Gateway URL: {gateway_url}")

    # Create browser toolkit with Cloudflare models
    try:
        browser_toolkit = BrowserToolkit(
            headless=True,  # Set to headless for better compatibility
            web_agent_model=models["content_researcher"],
            planning_agent_model=models["planning"],
        )
    except Exception as e:
        logger.warning(f"Browser toolkit initialization failed: {e}. Continuing without browser tools.")
        browser_toolkit = None

    # Create tools list
    tools = [SearchToolkit().search_duckduckgo]
    
    if browser_toolkit:
        tools.extend(browser_toolkit.get_tools())
        logger.info("Browser toolkit enabled")
    else:
        logger.info("Running without browser toolkit - search only mode")

    user_agent_kwargs = {
        "model": models["user"],
    }

    assistant_agent_kwargs = {
        "model": models["assistant"],
        "tools": tools,
    }

    task_kwargs = {
        "task_prompt": task,
        "with_task_specify": False,
    }

    society = RolePlaying(
        **task_kwargs,
        user_role_name="learner",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="learning_companion",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

    return society


def analyze_chat_history(chat_history):
    """Analyze chat history and extract tool call information."""
    print("\n============ Tool Call Analysis ============")
    logger.info("========== Starting tool call analysis ==========")

    tool_calls = []
    for i, message in enumerate(chat_history):
        if message.get("role") == "assistant" and "tool_calls" in message:
            for tool_call in message.get("tool_calls", []):
                if tool_call.get("type") == "function":
                    function = tool_call.get("function", {})
                    tool_info = {
                        "call_id": tool_call.get("id"),
                        "name": function.get("name"),
                        "arguments": function.get("arguments"),
                        "message_index": i,
                    }
                    tool_calls.append(tool_info)
                    print(
                        f"Tool Call: {function.get('name')} Args: {function.get('arguments')}"
                    )
                    logger.info(
                        f"Tool Call: {function.get('name')} Args: {function.get('arguments')}"
                    )

        elif message.get("role") == "tool" and "tool_call_id" in message:
            for tool_call in tool_calls:
                if tool_call.get("call_id") == message.get("tool_call_id"):
                    result = message.get("content", "")
                    result_summary = (
                        result[:100] + "..." if len(result) > 100 else result
                    )
                    print(
                        f"Tool Result: {tool_call.get('name')} Return: {result_summary}"
                    )
                    logger.info(
                        f"Tool Result: {tool_call.get('name')} Return: {result_summary}"
                    )

    print(f"Total tool calls found: {len(tool_calls)}")
    logger.info(f"Total tool calls found: {len(tool_calls)}")
    logger.info("========== Finished tool call analysis ==========")

    with open("learning_journey_cloudflare.json", "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)

    print("Records saved to learning_journey_cloudflare.json")
    print("============ Analysis Complete ============\n")


def run_learning_companion(task: str = None):
    """Run the learning companion with Cloudflare Workers AI.

    Args:
        task (str, optional): The learning task description. Defaults to an example task.
    """
    if task is None:
        task = """
        I want to learn about the transformers architecture in an LLM.  
        I've also taken a basic statistics course. 
        I have about 10 hours per week to dedicate to learning. Devise a roadmap for me.
        """

    print(f"🦉 Cloudflare Learning Assistant Starting")
    print(f"📚 Task: {task.strip()}")
    print(f"🔧 Model: {MODEL_TYPE}")
    print(f"=" * 60)

    try:
        society = construct_learning_society(task)

        from owl.utils import run_society

        answer, chat_history, token_count = run_society(society, round_limit=5)

        # Record tool usage history
        analyze_chat_history(chat_history)
        print(f"\033[94mAnswer: {answer}\033[0m")
        
        print(f"\n🎯 Learning Session Complete!")
        print(f"📊 Token usage: {token_count}")
        print(f"💾 Full history saved to learning_journey_cloudflare.json")
        
    except Exception as e:
        logger.error(f"Error running learning companion: {e}")
        print(f"❌ Error: {e}")
        raise


def main():
    """Main function to run from command line"""
    import sys
    
    if len(sys.argv) > 1:
        task = sys.argv[1]
    else:
        task = None
    
    run_learning_companion(task)


if __name__ == "__main__":
    main()