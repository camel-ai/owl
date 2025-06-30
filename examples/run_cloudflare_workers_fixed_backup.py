# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance wit"@h the License.
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
import logging
from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.toolkits import (
    CodeExecutionToolkit,
    ExcelToolkit,
    SearchToolkit,
    FileWriteToolkit,
)
from camel.types import ModelPlatformType
from camel.societies import RolePlaying
from camel.logger import set_log_level

from owl.utils import run_society, DocumentProcessingToolkit

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def construct_society(question: str) -> RolePlaying:
    """Construct a society of agents using Cloudflare Workers AI."""
    try:
        # Cloudflare Workers AI Gateway configuration
        cf_api_key = os.getenv("CF_API_TOKEN")
        cf_account_id = os.getenv("CF_ACCOUNT_ID")
        cf_gateway_name = os.getenv("CF_GATEWAY_NAME", "arya-ai")

        if not cf_api_key or not cf_account_id:
            raise ValueError(
                "CF_API_TOKEN and CF_ACCOUNT_ID must be set in environment variables"
            )

        # Model configurations
        model_type = os.getenv(
            "MODEL_TYPE", "cloudflare/@cf/meta/llama-4-scout-17b-16e-instruct"
        )  # Default model

        # Build the gateway URL - Direct Workers AI endpoint
        gateway_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/v1"
        
        # Debug: Print configuration (without sensitive data)
        logging.info(f"Cloudflare configuration: URL={gateway_url}, Model={model_type}")
        logging.info(f"API Key exists: {bool(cf_api_key)}, Length: {len(cf_api_key) if cf_api_key else 0}")
        temperature = float(os.getenv("TEMPERATURE", "0.8"))  # Default temperature
        max_tokens = int(os.getenv("MAX_TOKENS", "10000"))  # Default max_tokens - increased for Llama 4's 137k context window

        # Create models for different components
        model_config = {
            "temperature": temperature, 
            "max_tokens": max_tokens,
            "stream": False
        }
        
        models = {
            "user": ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
                model_type=model_type,
                api_key=cf_api_key,
                url=gateway_url,
                model_config_dict=model_config,
            ),
            "assistant": ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
                model_type=model_type,
                api_key=cf_api_key,
                url=gateway_url,
                model_config_dict=model_config,
            ),
            "planning": ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
                model_type=model_type,
                api_key=cf_api_key,
                url=gateway_url,
                model_config_dict=model_config,
            ),
        }

        # Configure toolkits with outputs directory for document generation
        output_dir = "./owl/outputs/"
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        tools = [
            *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
            SearchToolkit().search_duckduckgo,
            SearchToolkit().search_wiki,
            *ExcelToolkit().get_tools(),
            *FileWriteToolkit(output_dir=output_dir).get_tools(),
            # DocumentProcessingToolkit temporarily removed due to OPENAI_API_KEY dependency
        ]
        
        logging.info(f"FileWriteToolkit configured with output_dir: {output_dir}")
        logging.info(f"Available tools: {[tool.name for tool in tools if hasattr(tool, 'name')]}")

        # Configure agent roles and parameters
        user_agent_kwargs = {"model": models["user"]}
        assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}

        # Configure task parameters with document generation instructions
        enhanced_task_prompt = f"""
{question}

CRITICAL: You have access to a write_to_file tool that MUST be used to save results.

MANDATORY FILE CREATION STEPS:
1. When you need to save content, directly invoke the write_to_file tool
2. Use descriptive filenames with timestamps (e.g., result_20250625_144500.txt)
3. Save to the current directory (files will automatically go to owl/outputs/)
4. Create both a summary (.md) and main result file
5. VERIFY each file creation by checking the tool response

TOOL USAGE: When creating files, actually call the write_to_file function with:
- content: your text content
- filename: descriptive name with timestamp

You MUST create at least one file before completing the task.
"""
        
        task_kwargs = {
            "task_prompt": enhanced_task_prompt,
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

        logging.info("Society constructed successfully.")
        return society

    except ValueError as ve:
        logging.error(f"Configuration error: {ve}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise


def main():
    """Main function to run the OWL system with Cloudflare Workers AI."""
    # Check if CF_API_TOKEN and CF_ACCOUNT_ID are set
    if not os.getenv("CF_API_TOKEN") or not os.getenv("CF_ACCOUNT_ID"):
        logging.error(
            "CF_API_TOKEN and CF_ACCOUNT_ID must be set in environment variables"
        )
        print(
            "Error: CF_API_TOKEN and CF_ACCOUNT_ID must be set in environment variables"
        )
        sys.exit(1)

    # Example task
    default_task = "Create a Python script that calculates the Fibonacci sequence up to 20 numbers, save it as fibonacci.py, and run it."

    # Override default task if command line argument is provided
    task = sys.argv[1] if len(sys.argv) > 1 else default_task

    # Construct and run the society
    try:
        society = construct_society(task)
        answer, chat_history, token_count = run_society(society, round_limit=25)

        # Output the result
        print(f"\033[94mAnswer: {answer}\033[0m")

    except Exception as e:
        logging.error(f"Failed to run society: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()