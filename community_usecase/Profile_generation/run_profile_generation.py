import argparse
import json
import logging
import os
import pathlib
import re
import sys

from dotenv import load_dotenv

from camel.logger import get_logger, set_log_level
from camel.models import ModelFactory
from camel.societies import RolePlaying
from camel.toolkits import (
    BrowserToolkit,
    SearchToolkit,
)
from camel.types import ModelPlatformType

base_dir = pathlib.Path(__file__).parent.parent.parent
env_path = base_dir / "owl" / ".env"
print(env_path)
load_dotenv(dotenv_path=str(env_path))
set_log_level(level="DEBUG")
logger = get_logger(__name__)

file_handler = logging.FileHandler("process_history.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)


def construct_society(task: str) -> RolePlaying:
    """Construct a society of agents for the profile generation.

    Args:
        task (str): The personal information including the name and
        corresponding websites.

    Returns:
        RolePlaying: A configured society of agents for the profile
        generation.
    """
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="gpt-4.1",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.4},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="gpt-4.1",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.4},
        ),
        "content_researcher": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="gpt-4.1",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.2},
        ),
        "planning": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="gpt-4.1",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.3},
        ),
    }

    browser_toolkit = BrowserToolkit(
        headless=False,
        web_agent_model=models["content_researcher"],
        planning_agent_model=models["planning"],
        channel='chromium',
    )

    tools = [
        *browser_toolkit.get_tools(),
        SearchToolkit().search_duckduckgo,
    ]

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
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="Information_retriever",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

    return society


def analyze_chat_history(chat_history, filename='profile.html'):
    """Parse the chat history to extract queried URLs
    and associated HTML content."""

    print("\n============ URL Analysis ============")
    logger.info("========== Starting URL analysis ==========")

    queried_urls = []
    for entry in chat_history:
        for tool_call in entry.get("tool_calls", []):
            if tool_call.get("tool_name") == "browse_url":
                args = tool_call.get("args", {})
                url = args.get("start_url")
                if url:
                    queried_urls.append(url)

    url_count = len(queried_urls)

    print(f"Total queried URLs found: {url_count}")
    logger.info(f"Total queried URLs found: {url_count}")

    print("List of queried URLs:")
    logger.info("List of queried URLs:")
    for url in queried_urls:
        print(url)
        logger.info(url)

    last_html_content = None

    for item in reversed(chat_history):
        assistant_content = item.get("assistant", "")
        if (
            isinstance(assistant_content, str)
            and "```html" in assistant_content
        ):
            matches = re.findall(
                r"```html\s*(.*?)\s*```", assistant_content, re.DOTALL
            )
            if matches:
                last_html_content = matches[-1]
                break

    if last_html_content:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(last_html_content)
        print(f"\033[92mExtracted HTML saved to {filename}\033[0m")
    else:
        print("\033[91mNo HTML block found in chat history.\033[0m")

    with open("process_history.json", "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)

    print("Records saved to process_history.json")
    print("============ Analysis Complete ============\n")


def run_profile_generation(task: str | None = None):
    """Run the profile_generation with the given task.

    Args:
        task (str, optional): The personal information.
        Defaults to an example task.
    """
    if not task:
        task = """
find Bernard-Ghanem's information and generate a html page based on these 
websites:
https://www.linkedin.com/in/bernardghanem/
https://scholar.google.com/citations?hl=en&user=rVsGTeEAAAAJ&view_op=list_works
https://x.com/bernardsghanem
https://www.researchgate.net/profile/Bernard-Ghanem
https://www.bernardghanem.com/curriculum-vitae
https://www.bernardghanem.com/home
        """
    html_prompt = """
Generate a professional and natural-looking personal profile HTML page based 
on the provided information, following these detailed requirements:

Use standard HTML5 structure.

Layout should be clearly organized using <h1> for the main title, <h2> for 
section headings, and <p> for paragraph text.

Use proper <a href> hyperlinks for any external links (e.g., LinkedIn, 
ResearchGate, Google Scholar).

Write in a natural, flowing narrative style suitable for introducing the 
person to a broad audience (no bullet points).

Strictly follow the given content structure:

Personal Information (Name, Positions, Contact( include social media), 
Research Keywords)

Summary (Short description of expertise and overall role)

Biography (Detailed career history (can be found in Linkedin) and research 
focus)

Research Interests (Areas of active research)

Awards and Distinctions (Honors and recognitions)

Education (Academic degrees in order)

Engage / Related Links (Professional profiles and external resources)

The final HTML should look clean, modern, and ready to be used as a complete 
professional personal page.
    """

    society = construct_society(task + html_prompt)

    from owl.utils import run_society

    answer, chat_history, token_count = run_society(society, round_limit=9)

    analyze_chat_history(chat_history)
    print(f"\033[94mAnswer: {answer}\033[0m")
    print(f"\033[94mToken_count: {token_count}\033[0m")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a personal profile page."
    )
    parser.add_argument('--task', type=str, help='The personal information.')
    args = parser.parse_args()

    run_profile_generation(task=args.task)
