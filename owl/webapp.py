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
# Import from the correct module path
from utils import run_society
import os
import gradio as gr
import time
import json
import logging
import datetime
from typing import Tuple
import importlib
from dotenv import load_dotenv, set_key, find_dotenv, unset_key
import threading
import queue
import re

os.environ["PYTHONIOENCODING"] = "utf-8"


# Configure logging system
def setup_logging():
    """Configure logging system to output logs to file, memory queue, and console"""
    # Create logs directory (if it doesn't exist)
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Generate log filename (using current date)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"gradio_log_{current_date}.txt")

    # Configure root logger (captures all logs)
    root_logger = logging.getLogger()

    # Clear existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(logging.INFO)

    # Create file handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("Logging system initialized, log file: %s", log_file)
    return log_file


# Global variables
LOG_FILE = None
LOG_QUEUE: queue.Queue = queue.Queue()  # Log queue
STOP_LOG_THREAD = threading.Event()
CURRENT_PROCESS = None  # Used to track the currently running process
STOP_REQUESTED = threading.Event()  # Used to mark if stop was requested


# Log reading and updating functions
def log_reader_thread(log_file):
    """Background thread that continuously reads the log file and adds new lines to the queue"""
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # Move to the end of file
            f.seek(0, 2)

            while not STOP_LOG_THREAD.is_set():
                line = f.readline()
                if line:
                    LOG_QUEUE.put(line)  # Add to conversation record queue
                else:
                    # No new lines, wait for a short time
                    time.sleep(0.1)
    except Exception as e:
        logging.error(f"Log reader thread error: {str(e)}")


def get_latest_logs(max_lines=100, queue_source=None):
    """Get the latest log lines from the queue, or read directly from the file if the queue is empty

    Args:
        max_lines: Maximum number of lines to return
        queue_source: Specify which queue to use, default is LOG_QUEUE

    Returns:
        str: Log content
    """
    logs = []
    log_queue = queue_source if queue_source else LOG_QUEUE

    # Create a temporary queue to store logs so we can process them without removing them from the original queue
    temp_queue = queue.Queue()
    temp_logs = []

    try:
        # Try to get all available log lines from the queue
        while not log_queue.empty() and len(temp_logs) < max_lines:
            log = log_queue.get_nowait()
            temp_logs.append(log)
            temp_queue.put(log)  # Put the log back into the temporary queue
    except queue.Empty:
        pass

    # Process conversation records
    logs = temp_logs

    # If there are no new logs or not enough logs, try to read the last few lines directly from the file
    if len(logs) < max_lines and LOG_FILE and os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                # If there are already some logs in the queue, only read the remaining needed lines
                remaining_lines = max_lines - len(logs)
                file_logs = (
                    all_lines[-remaining_lines:]
                    if len(all_lines) > remaining_lines
                    else all_lines
                )

                # Add file logs before queue logs
                logs = file_logs + logs
        except Exception as e:
            error_msg = f"Error reading log file: {str(e)}"
            logging.error(error_msg)
            if not logs:  # Only add error message if there are no logs
                logs = [error_msg]

    # If there are still no logs, return a prompt message
    if not logs:
        return "Initialization in progress..."

    # Filter logs, only keep logs with 'camel.agents.chat_agent - INFO'
    filtered_logs = []
    for log in logs:
        if "camel.agents.chat_agent - INFO" in log:
            filtered_logs.append(log)

    # If there are no logs after filtering, return a prompt message
    if not filtered_logs:
        return "No conversation records yet."

    # Process log content, extract the latest user and assistant messages
    simplified_logs = []

    # Use a set to track messages that have already been processed, to avoid duplicates
    processed_messages = set()

    def process_message(role, content):
        # Create a unique identifier to track messages
        msg_id = f"{role}:{content}"
        if msg_id in processed_messages:
            return None

        processed_messages.add(msg_id)
        content = content.replace("\\n", "\n")
        lines = [line.strip() for line in content.split("\n")]
        content = "\n".join(lines)

        role_emoji = "🙋" if role.lower() == "user" else "🤖"
        return f"""### {role_emoji} {role.title()} Agent

{content}"""

    for log in filtered_logs:
        formatted_messages = []
        # Try to extract message array
        messages_match = re.search(
            r"Model (.*?), index (\d+), processed these messages: (\[.*\])", log
        )

        if messages_match:
            try:
                messages = json.loads(messages_match.group(3))
                for msg in messages:
                    if msg.get("role") in ["user", "assistant"]:
                        formatted_msg = process_message(
                            msg.get("role"), msg.get("content", "")
                        )
                        if formatted_msg:
                            formatted_messages.append(formatted_msg)
            except json.JSONDecodeError:
                pass

        # If JSON parsing fails or no message array is found, try to extract conversation content directly
        if not formatted_messages:
            user_pattern = re.compile(r"\{'role': 'user', 'content': '(.*?)'\}")
            assistant_pattern = re.compile(
                r"\{'role': 'assistant', 'content': '(.*?)'\}"
            )

            for content in user_pattern.findall(log):
                formatted_msg = process_message("user", content)
                if formatted_msg:
                    formatted_messages.append(formatted_msg)

            for content in assistant_pattern.findall(log):
                formatted_msg = process_message("assistant", content)
                if formatted_msg:
                    formatted_messages.append(formatted_msg)

        if formatted_messages:
            simplified_logs.append("\n\n".join(formatted_messages))

    # Format log output, ensure appropriate separation between each conversation record
    formatted_logs = []
    for i, log in enumerate(simplified_logs):
        # Remove excess whitespace characters from beginning and end
        log = log.strip()

        formatted_logs.append(log)

        # Ensure each conversation record ends with a newline
        if not log.endswith("\n"):
            formatted_logs.append("\n")

    return "\n".join(formatted_logs)


# Dictionary containing module descriptions
MODULE_DESCRIPTIONS = {
    "run": "Default mode: Using OpenAI model's default agent collaboration mode, suitable for most tasks.",
    "run_mini": "Using OpenAI model with minimal configuration to process tasks",
    "run_gemini": "Using Gemini model to process tasks",
    "run_deepseek_zh": "Using deepseek model to process Chinese tasks",
    "run_openai_compatible_model": "Using openai compatible model to process tasks",
    "run_ollama": "Using local ollama model to process tasks",
    "run_qwen_mini_zh": "Using qwen model with minimal configuration to process tasks",
    "run_qwen_zh": "Using qwen model to process tasks",
    "run_azure_openai": "Using azure openai model to process tasks",
    "run_groq": "Using groq model to process tasks",
}


# Default environment variable template
DEFAULT_ENV_TEMPLATE = """#===========================================
# MODEL & API 
# (See https://docs.camel-ai.org/key_modules/models.html#)
#===========================================

# OPENAI API (https://platform.openai.com/api-keys)
OPENAI_API_KEY='Your_Key'
# OPENAI_API_BASE_URL=""

# Azure OpenAI API
# AZURE_OPENAI_BASE_URL=""
# AZURE_API_VERSION=""
# AZURE_OPENAI_API_KEY=""
# AZURE_DEPLOYMENT_NAME=""


# Qwen API (https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key)
QWEN_API_KEY='Your_Key'

# DeepSeek API (https://platform.deepseek.com/api_keys)
DEEPSEEK_API_KEY='Your_Key'

#===========================================
# Tools & Services API
#===========================================

# Google Search API (https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3)
GOOGLE_API_KEY='Your_Key'
SEARCH_ENGINE_ID='Your_ID'

# Chunkr API (https://chunkr.ai/)
CHUNKR_API_KEY='Your_Key'

# Firecrawl API (https://www.firecrawl.dev/)
FIRECRAWL_API_KEY='Your_Key'
#FIRECRAWL_API_URL="https://api.firecrawl.dev"
"""


def validate_input(question: str) -> bool:
    """Validate if user input is valid

    Args:
        question: User question

    Returns:
        bool: Whether the input is valid
    """
    # Check if input is empty or contains only spaces
    if not question or question.strip() == "":
        return False
    return True


def run_owl(question: str, example_module: str) -> Tuple[str, str, str]:
    """Run the OWL system and return results

    Args:
        question: User question
        example_module: Example module name to import (e.g., "run_terminal_zh" or "run_deep")

    Returns:
        Tuple[...]: Answer, token count, status
    """
    global CURRENT_PROCESS

    # Validate input
    if not validate_input(question):
        logging.warning("User submitted invalid input")
        return (
            "Please enter a valid question",
            "0",
            "❌ Error: Invalid input question",
        )

    try:
        # Ensure environment variables are loaded
        load_dotenv(find_dotenv(), override=True)
        logging.info(
            f"Processing question: '{question}', using module: {example_module}"
        )

        # Check if the module is in MODULE_DESCRIPTIONS
        if example_module not in MODULE_DESCRIPTIONS:
            logging.error(f"User selected an unsupported module: {example_module}")
            return (
                f"Selected module '{example_module}' is not supported",
                "0",
                "❌ Error: Unsupported module",
            )

        # Dynamically import target module
        module_path = f"examples.{example_module}"
        try:
            logging.info(f"Importing module: {module_path}")
            module = importlib.import_module(module_path)
        except ImportError as ie:
            logging.error(f"Unable to import module {module_path}: {str(ie)}")
            return (
                f"Unable to import module: {module_path}",
                "0",
                f"❌ Error: Module {example_module} does not exist or cannot be loaded - {str(ie)}",
            )
        except Exception as e:
            logging.error(
                f"Error occurred while importing module {module_path}: {str(e)}"
            )
            return (
                f"Error occurred while importing module: {module_path}",
                "0",
                f"❌ Error: {str(e)}",
            )

        # Check if it contains the construct_society function
        if not hasattr(module, "construct_society"):
            logging.error(
                f"construct_society function not found in module {module_path}"
            )
            return (
                f"construct_society function not found in module {module_path}",
                "0",
                "❌ Error: Module interface incompatible",
            )

        # Build society simulation
        try:
            logging.info("Building society simulation...")
            society = module.construct_society(question)

        except Exception as e:
            logging.error(f"Error occurred while building society simulation: {str(e)}")
            return (
                f"Error occurred while building society simulation: {str(e)}",
                "0",
                f"❌ Error: Build failed - {str(e)}",
            )

        # Run society simulation
        try:
            logging.info("Running society simulation...")
            answer, chat_history, token_info = run_society(society)
            logging.info("Society simulation completed")
        except Exception as e:
            logging.error(f"Error occurred while running society simulation: {str(e)}")
            return (
                f"Error occurred while running society simulation: {str(e)}",
                "0",
                f"❌ Error: Run failed - {str(e)}",
            )

        # Safely get token count
        if not isinstance(token_info, dict):
            token_info = {}

        completion_tokens = token_info.get("completion_token_count", 0)
        prompt_tokens = token_info.get("prompt_token_count", 0)
        total_tokens = completion_tokens + prompt_tokens

        logging.info(
            f"Processing completed, token usage: completion={completion_tokens}, prompt={prompt_tokens}, total={total_tokens}"
        )

        return (
            answer,
            f"Completion tokens: {completion_tokens:,} | Prompt tokens: {prompt_tokens:,} | Total: {total_tokens:,}",
            "✅ Successfully completed",
        )

    except Exception as e:
        logging.error(
            f"Uncaught error occurred while processing the question: {str(e)}"
        )
        return (f"Error occurred: {str(e)}", "0", f"❌ Error: {str(e)}")


def update_module_description(module_name: str) -> str:
    """Return the description of the selected module"""
    return MODULE_DESCRIPTIONS.get(module_name, "No description available")


# Store environment variables configured from the frontend
WEB_FRONTEND_ENV_VARS: dict[str, str] = {}


def init_env_file():
    """Initialize .env file if it doesn't exist"""
    dotenv_path = find_dotenv()
    if not dotenv_path:
        with open(".env", "w") as f:
            f.write(DEFAULT_ENV_TEMPLATE)
        dotenv_path = find_dotenv()
    return dotenv_path


def load_env_vars():
    """Load environment variables and return as dictionary format

    Returns:
        dict: Environment variable dictionary, each value is a tuple containing value and source (value, source)
    """
    dotenv_path = init_env_file()
    load_dotenv(dotenv_path, override=True)

    # Read environment variables from .env file
    env_file_vars = {}
    with open(dotenv_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_file_vars[key.strip()] = value.strip().strip("\"'")

    # Get from system environment variables
    system_env_vars = {
        k: v
        for k, v in os.environ.items()
        if k not in env_file_vars and k not in WEB_FRONTEND_ENV_VARS
    }

    # Merge environment variables and mark sources
    env_vars = {}

    # Add system environment variables (lowest priority)
    for key, value in system_env_vars.items():
        env_vars[key] = (value, "System")

    # Add .env file environment variables (medium priority)
    for key, value in env_file_vars.items():
        env_vars[key] = (value, ".env file")

    # Add frontend configured environment variables (highest priority)
    for key, value in WEB_FRONTEND_ENV_VARS.items():
        env_vars[key] = (value, "Frontend configuration")
        # Ensure operating system environment variables are also updated
        os.environ[key] = value

    return env_vars


def save_env_vars(env_vars):
    """Save environment variables to .env file

    Args:
        env_vars: Dictionary, keys are environment variable names, values can be strings or (value, source) tuples
    """
    try:
        dotenv_path = init_env_file()

        # Save each environment variable
        for key, value_data in env_vars.items():
            if key and key.strip():  # Ensure key is not empty
                # Handle case where value might be a tuple
                if isinstance(value_data, tuple):
                    value = value_data[0]
                else:
                    value = value_data

                set_key(dotenv_path, key.strip(), value.strip())

        # Reload environment variables to ensure they take effect
        load_dotenv(dotenv_path, override=True)

        return True, "Environment variables have been successfully saved!"
    except Exception as e:
        return False, f"Error saving environment variables: {str(e)}"


def add_env_var(key, value, from_frontend=True):
    """Add or update a single environment variable

    Args:
        key: Environment variable name
        value: Environment variable value
        from_frontend: Whether it's from frontend configuration, default is True
    """
    try:
        if not key or not key.strip():
            return False, "Variable name cannot be empty"

        key = key.strip()
        value = value.strip()

        # If from frontend, add to frontend environment variable dictionary
        if from_frontend:
            WEB_FRONTEND_ENV_VARS[key] = value
            # Directly update system environment variables
            os.environ[key] = value

        # Also update .env file
        dotenv_path = init_env_file()
        set_key(dotenv_path, key, value)
        load_dotenv(dotenv_path, override=True)

        return True, f"Environment variable {key} has been successfully added/updated!"
    except Exception as e:
        return False, f"Error adding environment variable: {str(e)}"


def delete_env_var(key):
    """Delete environment variable"""
    try:
        if not key or not key.strip():
            return False, "Variable name cannot be empty"

        key = key.strip()

        # Delete from .env file
        dotenv_path = init_env_file()
        unset_key(dotenv_path, key)

        # Delete from frontend environment variable dictionary
        if key in WEB_FRONTEND_ENV_VARS:
            del WEB_FRONTEND_ENV_VARS[key]

        # Also delete from current process environment
        if key in os.environ:
            del os.environ[key]

        return True, f"Environment variable {key} has been successfully deleted!"
    except Exception as e:
        return False, f"Error deleting environment variable: {str(e)}"


def is_api_related(key: str) -> bool:
    """Determine if an environment variable is API-related

    Args:
        key: Environment variable name

    Returns:
        bool: Whether it's API-related
    """
    # API-related keywords
    api_keywords = [
        "api",
        "key",
        "token",
        "secret",
        "password",
        "openai",
        "qwen",
        "deepseek",
        "google",
        "search",
        "hf",
        "hugging",
        "chunkr",
        "firecrawl",
    ]

    # Check if it contains API-related keywords (case insensitive)
    return any(keyword in key.lower() for keyword in api_keywords)


def get_api_guide(key: str) -> str:
    """Return the corresponding API guide based on the environment variable name

    Args:
        key: Environment variable name

    Returns:
        str: API guide link or description
    """
    key_lower = key.lower()
    if "openai" in key_lower:
        return "https://platform.openai.com/api-keys"
    elif "qwen" in key_lower or "dashscope" in key_lower:
        return "https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key"
    elif "deepseek" in key_lower:
        return "https://platform.deepseek.com/api_keys"
    elif "google" in key_lower:
        return "https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3"
    elif "search_engine_id" in key_lower:
        return "https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3"
    elif "chunkr" in key_lower:
        return "https://chunkr.ai/"
    elif "firecrawl" in key_lower:
        return "https://www.firecrawl.dev/"
    else:
        return ""


def update_env_table():
    """Update environment variable table display, only showing API-related environment variables"""
    env_vars = load_env_vars()
    # Filter out API-related environment variables
    api_env_vars = {k: v for k, v in env_vars.items() if is_api_related(k)}
    # Convert to list format to meet Gradio Dataframe requirements
    # Format: [Variable name, Variable value, Guide link]
    result = []
    for k, v in api_env_vars.items():
        guide = get_api_guide(k)
        # If there's a guide link, create a clickable link
        guide_link = (
            f"<a href='{guide}' target='_blank' class='guide-link'>🔗 Get</a>"
            if guide
            else ""
        )
        result.append([k, v[0], guide_link])
    return result


def save_env_table_changes(data):
    """Save changes to the environment variable table

    Args:
        data: Dataframe data, possibly a pandas DataFrame object

    Returns:
        str: Operation status information, containing HTML-formatted status message
    """
    try:
        logging.info(
            f"Starting to process environment variable table data, type: {type(data)}"
        )

        # Get all current environment variables
        current_env_vars = load_env_vars()
        processed_keys = set()  # Record processed keys to detect deleted variables

        # Process pandas DataFrame object
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            # Get column name information
            columns = data.columns.tolist()
            logging.info(f"DataFrame column names: {columns}")

            # Iterate through each row of the DataFrame
            for index, row in data.iterrows():
                # Use column names to access data
                if len(columns) >= 3:
                    # Get variable name and value (column 0 is name, column 1 is value)
                    key = row[0] if isinstance(row, pd.Series) else row.iloc[0]
                    value = row[1] if isinstance(row, pd.Series) else row.iloc[1]

                    # Check if it's an empty row or deleted variable
                    if (
                        key and str(key).strip()
                    ):  # If key name is not empty, add or update
                        logging.info(
                            f"Processing environment variable: {key} = {value}"
                        )
                        add_env_var(key, str(value))
                        processed_keys.add(key)
        # Process other formats
        elif isinstance(data, dict):
            logging.info(f"Dictionary format data keys: {list(data.keys())}")
            # If dictionary format, try different keys
            if "data" in data:
                rows = data["data"]
            elif "values" in data:
                rows = data["values"]
            elif "value" in data:
                rows = data["value"]
            else:
                # Try using dictionary directly as row data
                rows = []
                for key, value in data.items():
                    if key not in ["headers", "types", "columns"]:
                        rows.append([key, value])

            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, list) and len(row) >= 2:
                        key, value = row[0], row[1]
                        if key and str(key).strip():
                            add_env_var(key, str(value))
                            processed_keys.add(key)
        elif isinstance(data, list):
            # 列表格式
            for row in data:
                if isinstance(row, list) and len(row) >= 2:
                    key, value = row[0], row[1]
                    if key and str(key).strip():
                        add_env_var(key, str(value))
                        processed_keys.add(key)
        else:
            logging.error(f"Unknown data format: {type(data)}")
            return f"❌ Save failed: Unknown data format {type(data)}"

        # Process deleted variables - check if there are variables in current environment not appearing in the table
        api_related_keys = {k for k in current_env_vars.keys() if is_api_related(k)}
        keys_to_delete = api_related_keys - processed_keys

        # Delete variables no longer in the table
        for key in keys_to_delete:
            logging.info(f"Deleting environment variable: {key}")
            delete_env_var(key)

        return "✅ Environment variables have been successfully saved"
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logging.error(f"Error saving environment variables: {str(e)}\n{error_details}")
        return f"❌ Save failed: {str(e)}"


def get_env_var_value(key):
    """Get the actual value of an environment variable

    Priority: Frontend configuration > .env file > System environment variables
    """
    # Check frontend configured environment variables
    if key in WEB_FRONTEND_ENV_VARS:
        return WEB_FRONTEND_ENV_VARS[key]

    # Check system environment variables (including those loaded from .env)
    return os.environ.get(key, "")


def create_ui():
    """Create enhanced Gradio interface"""

    def clear_log_file():
        """Clear log file content"""
        try:
            if LOG_FILE and os.path.exists(LOG_FILE):
                # Clear log file content instead of deleting the file
                open(LOG_FILE, "w").close()
                logging.info("Log file has been cleared")
                # Clear log queue
                while not LOG_QUEUE.empty():
                    try:
                        LOG_QUEUE.get_nowait()
                    except queue.Empty:
                        break
                return ""
            else:
                return ""
        except Exception as e:
            logging.error(f"Error clearing log file: {str(e)}")
            return ""

    # Create a real-time log update function
    def process_with_live_logs(question, module_name):
        """Process questions and update logs in real-time"""
        global CURRENT_PROCESS

        # Clear log file
        clear_log_file()

        # Create a background thread to process the question
        result_queue = queue.Queue()

        def process_in_background():
            try:
                result = run_owl(question, module_name)
                result_queue.put(result)
            except Exception as e:
                result_queue.put(
                    (f"Error occurred: {str(e)}", "0", f"❌ Error: {str(e)}")
                )

        # Start background processing thread
        bg_thread = threading.Thread(target=process_in_background)
        CURRENT_PROCESS = bg_thread  # Record current process
        bg_thread.start()

        # While waiting for processing to complete, update logs once per second
        while bg_thread.is_alive():
            # Update conversation record display
            logs2 = get_latest_logs(100, LOG_QUEUE)

            # Always update status
            yield (
                "0",
                "<span class='status-indicator status-running'></span> Processing...",
                logs2,
            )

            time.sleep(1)

        # Processing complete, get results
        if not result_queue.empty():
            result = result_queue.get()
            answer, token_count, status = result

            # Final update of conversation record
            logs2 = get_latest_logs(100, LOG_QUEUE)

            # Set different indicators based on status
            if "Error" in status:
                status_with_indicator = (
                    f"<span class='status-indicator status-error'></span> {status}"
                )
            else:
                status_with_indicator = (
                    f"<span class='status-indicator status-success'></span> {status}"
                )

            yield token_count, status_with_indicator, logs2
        else:
            logs2 = get_latest_logs(100, LOG_QUEUE)
            yield (
                "0",
                "<span class='status-indicator status-error'></span> Terminated",
                logs2,
            )

    with gr.Blocks(title="OWL", theme=gr.themes.Soft(primary_hue="blue")) as app:
        gr.Markdown(
            """
                # 🦉 OWL Multi-Agent Collaboration System

                Advanced multi-agent collaboration system developed based on the CAMEL framework, designed to solve complex problems through agent collaboration.

                Models and tools can be customized by modifying local scripts.
                
                This web app is currently in beta development. It is provided for demonstration and testing purposes only and is not yet recommended for production use.
                """
        )

        # Add custom CSS
        gr.HTML("""
            <style>
            /* Chat container style */
            .chat-container .chatbot {
                height: 500px;
                overflow-y: auto;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            

            /* Improved tab style */
            .tabs .tab-nav {
                background-color: #f5f5f5;
                border-radius: 8px 8px 0 0;
                padding: 5px;
            }
            
            .tabs .tab-nav button {
                border-radius: 5px;
                margin: 0 3px;
                padding: 8px 15px;
                font-weight: 500;
            }
            
            .tabs .tab-nav button.selected {
                background-color: #2c7be5;
                color: white;
            }
            
            /* Status indicator style */
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
            }
            
            .status-running {
                background-color: #ffc107;
                animation: pulse 1.5s infinite;
            }
            
            .status-success {
                background-color: #28a745;
            }
            
            .status-error {
                background-color: #dc3545;
            }
            
            /* Log display area style */
            .log-display textarea {
                height: 400px !important;
                max-height: 400px !important;
                overflow-y: auto !important;
                font-family: monospace;
                font-size: 0.9em;
                white-space: pre-wrap;
                line-height: 1.4;
            }
            
            .log-display {
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                min-height: 50vh;
                max-height: 75vh;
            }
            
            /* Environment variable management style */
            .env-manager-container {
                border-radius: 10px;
                padding: 15px;
                background-color: #f9f9f9;
                margin-bottom: 20px;
            }
            
            .env-controls, .api-help-container {
                border-radius: 8px;
                padding: 15px;
                background-color: white;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
                height: 100%;
            }
            
            .env-add-group, .env-delete-group {
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                background-color: #f5f8ff;
                border: 1px solid #e0e8ff;
            }
            
            .env-delete-group {
                background-color: #fff5f5;
                border: 1px solid #ffe0e0;
            }
            
            .env-buttons {
                justify-content: flex-start;
                gap: 10px;
                margin-top: 10px;
            }
            
            .env-button {
                min-width: 100px;
            }
            
            .delete-button {
                background-color: #dc3545;
                color: white;
            }
            
            .env-table {
                margin-bottom: 15px;
            }
            
            /* Improved environment variable table style */
            .env-table table {
                border-collapse: separate;
                border-spacing: 0;
                width: 100%;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
            
            .env-table th {
                background-color: #f0f7ff;
                padding: 12px 15px;
                text-align: left;
                font-weight: 600;
                color: #2c7be5;
                border-bottom: 2px solid #e0e8ff;
            }
            
            .env-table td {
                padding: 10px 15px;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .env-table tr:hover td {
                background-color: #f9fbff;
            }
            
            .env-table tr:last-child td {
                border-bottom: none;
            }
            
            /* Status icon style */
            .status-icon-cell {
                text-align: center;
                font-size: 1.2em;
            }
            
            /* Link style */
            .guide-link {
                color: #2c7be5;
                text-decoration: none;
                cursor: pointer;
                font-weight: 500;
            }
            
            .guide-link:hover {
                text-decoration: underline;
            }
            
            .env-status {
                margin-top: 15px;
                font-weight: 500;
                padding: 10px;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            
            .env-status-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .env-status-error {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .api-help-accordion {
                margin-bottom: 8px;
                border-radius: 6px;
                overflow: hidden;
            }
            

            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            </style>
            """)

        with gr.Row():
            with gr.Column(scale=0.5):
                question_input = gr.Textbox(
                    lines=5,
                    placeholder="Please enter your question...",
                    label="Question",
                    elem_id="question_input",
                    show_copy_button=True,
                    value="Open Google search, summarize the github stars, fork counts, etc. of camel-ai's camel framework, and write the numbers into a python file using the plot package, save it locally, and run the generated python file.",
                )

                # Enhanced module selection dropdown
                # Only includes modules defined in MODULE_DESCRIPTIONS
                module_dropdown = gr.Dropdown(
                    choices=list(MODULE_DESCRIPTIONS.keys()),
                    value="run",
                    label="Select Function Module",
                    interactive=True,
                )

                # Module description text box
                module_description = gr.Textbox(
                    value=MODULE_DESCRIPTIONS["run"],
                    label="Module Description",
                    interactive=False,
                    elem_classes="module-info",
                )

                with gr.Row():
                    run_button = gr.Button(
                        "Run", variant="primary", elem_classes="primary"
                    )

                status_output = gr.HTML(
                    value="<span class='status-indicator status-success'></span> Ready",
                    label="Status",
                )
                token_count_output = gr.Textbox(
                    label="Token Count", interactive=False, elem_classes="token-count"
                )

                # Example questions
                examples = [
                    "Open Google search, summarize the github stars, fork counts, etc. of camel-ai's camel framework, and write the numbers into a python file using the plot package, save it locally, and run the generated python file.",
                    "Browse Amazon and find a product that is attractive to programmers. Please provide the product name and price",
                    "Write a hello world python file and save it locally",
                ]

                gr.Examples(examples=examples, inputs=question_input)

                gr.HTML("""
                        <div class="footer" id="about">
                            <h3>About OWL Multi-Agent Collaboration System</h3>
                            <p>OWL is an advanced multi-agent collaboration system developed based on the CAMEL framework, designed to solve complex problems through agent collaboration.</p>
                            <p>© 2025 CAMEL-AI.org. Based on Apache License 2.0 open source license</p>
                            <p><a href="https://github.com/camel-ai/owl" target="_blank">GitHub</a></p>
                        </div>
                    """)

            with gr.Tabs():  # Set conversation record as the default selected tab
                with gr.TabItem("Conversation Record"):
                    # Add conversation record display area
                    with gr.Box():
                        log_display2 = gr.Markdown(
                            value="No conversation records yet.",
                            elem_classes="log-display",
                        )

                    with gr.Row():
                        refresh_logs_button2 = gr.Button("Refresh Record")
                        auto_refresh_checkbox2 = gr.Checkbox(
                            label="Auto Refresh", value=True, interactive=True
                        )
                        clear_logs_button2 = gr.Button(
                            "Clear Record", variant="secondary"
                        )

                with gr.TabItem("Environment Variable Management", id="env-settings"):
                    with gr.Box(elem_classes="env-manager-container"):
                        gr.Markdown("""
                            ## Environment Variable Management
                            
                            Set model API keys and other service credentials here. This information will be saved in a local `.env` file, ensuring your API keys are securely stored and not uploaded to the network. Correctly setting API keys is crucial for the functionality of the OWL system. Environment variables can be flexibly configured according to tool requirements.
                            """)

                        # Main content divided into two-column layout
                        with gr.Row():
                            # Left column: Environment variable management controls
                            with gr.Column(scale=3):
                                with gr.Box(elem_classes="env-controls"):
                                    # Environment variable table - set to interactive for direct editing
                                    gr.Markdown("""
                                    <div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 10px; margin: 15px 0; border-radius: 4px;">
                                      <strong>Tip:</strong> Please make sure to run cp .env_template .env to create a local .env file, and flexibly configure the required environment variables according to the running module
                                    </div>
                                    """)

                                    # Enhanced environment variable table, supporting adding and deleting rows
                                    env_table = gr.Dataframe(
                                        headers=[
                                            "Variable Name",
                                            "Value",
                                            "Retrieval Guide",
                                        ],
                                        datatype=[
                                            "str",
                                            "str",
                                            "html",
                                        ],  # Set the last column as HTML type to support links
                                        row_count=10,  # Increase row count to allow adding new variables
                                        col_count=(3, "fixed"),
                                        value=update_env_table,
                                        label="API Keys and Environment Variables",
                                        interactive=True,  # Set as interactive, allowing direct editing
                                        elem_classes="env-table",
                                    )

                                    # Operation instructions
                                    gr.Markdown(
                                        """
                                    <div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 10px; margin: 15px 0; border-radius: 4px;">
                                    <strong>Operation Guide</strong>:
                                    <ul style="margin-top: 8px; margin-bottom: 8px;">
                                      <li><strong>Edit Variable</strong>: Click directly on the "Value" cell in the table to edit</li>
                                      <li><strong>Add Variable</strong>: Enter a new variable name and value in a blank row</li>
                                      <li><strong>Delete Variable</strong>: Clear the variable name to delete that row</li>
                                      <li><strong>Get API Key</strong>: Click on the link in the "Retrieval Guide" column to get the corresponding API key</li>
                                    </ul>
                                    </div>
                                    """,
                                        elem_classes="env-instructions",
                                    )

                                    # Environment variable operation buttons
                                    with gr.Row(elem_classes="env-buttons"):
                                        save_env_button = gr.Button(
                                            "💾 Save Changes",
                                            variant="primary",
                                            elem_classes="env-button",
                                        )
                                        refresh_button = gr.Button(
                                            "🔄 Refresh List", elem_classes="env-button"
                                        )

                                    # Status display
                                    env_status = gr.HTML(
                                        label="Operation Status",
                                        value="",
                                        elem_classes="env-status",
                                    )

                    # 连接事件处理函数
                    save_env_button.click(
                        fn=save_env_table_changes,
                        inputs=[env_table],
                        outputs=[env_status],
                    ).then(fn=update_env_table, outputs=[env_table])

                    refresh_button.click(fn=update_env_table, outputs=[env_table])

        # Set up event handling
        run_button.click(
            fn=process_with_live_logs,
            inputs=[question_input, module_dropdown],
            outputs=[token_count_output, status_output, log_display2],
        )

        # Module selection updates description
        module_dropdown.change(
            fn=update_module_description,
            inputs=module_dropdown,
            outputs=module_description,
        )

        # Conversation record related event handling
        refresh_logs_button2.click(
            fn=lambda: get_latest_logs(100, LOG_QUEUE), outputs=[log_display2]
        )

        clear_logs_button2.click(fn=clear_log_file, outputs=[log_display2])

        # Auto refresh control
        def toggle_auto_refresh(enabled):
            if enabled:
                return gr.update(every=3)
            else:
                return gr.update(every=0)

        auto_refresh_checkbox2.change(
            fn=toggle_auto_refresh,
            inputs=[auto_refresh_checkbox2],
            outputs=[log_display2],
        )

        # No longer automatically refresh logs by default

    return app


# Main function
def main():
    try:
        # Initialize logging system
        global LOG_FILE
        LOG_FILE = setup_logging()
        logging.info("OWL Web application started")

        # Start log reading thread
        log_thread = threading.Thread(
            target=log_reader_thread, args=(LOG_FILE,), daemon=True
        )
        log_thread.start()
        logging.info("Log reading thread started")

        # Initialize .env file (if it doesn't exist)
        init_env_file()
        app = create_ui()

        app.queue()
        app.launch(share=False, favicon_path="../assets/owl-favicon.ico")
    except Exception as e:
        logging.error(f"Error occurred while starting the application: {str(e)}")
        print(f"Error occurred while starting the application: {str(e)}")
        import traceback

        traceback.print_exc()

    finally:
        # Ensure log thread stops
        STOP_LOG_THREAD.set()
        STOP_REQUESTED.set()
        logging.info("Application closed")


if __name__ == "__main__":
    main()
