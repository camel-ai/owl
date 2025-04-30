import argparse
import json
import logging
import os
import pathlib
import re
import sys
from owl.utils import run_society
from pydantic import BaseModel
from dotenv import load_dotenv
from camel.agents import ChatAgent
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
    """Create a Role‑Playing society of agents able to browse, search and
    retrieve profile information for the given task string.

    Parameters
    ----------
    task : str
        Task prompt that contains the person name and seed URLs.

    Returns
    -------
    RolePlaying
        Configured society ready to be executed with `run_society`.
    """
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="gpt-4.1",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.4},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="gpt-4.1",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.4},
        ),
        "content_researcher": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="gpt-4.1",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.2},
        ),
        "planning": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="gpt-4.1",
            api_key=os.getenv("OPENAI_API_KEY"),
            model_config_dict={"temperature": 0.3},
        ),
    }

    browser_toolkit = BrowserToolkit(
        headless=False,
        web_agent_model=models["content_researcher"],
        planning_agent_model=models["planning"],
        channel="chromium",
        user_data_dir=r"C:\Users\13033\playwright_user_data",
    )

    tools = [
        *browser_toolkit.get_tools(),
        SearchToolkit().search_duckduckgo,
    ]

    society = RolePlaying(
        task_prompt=task,
        with_task_specify=False,
        user_role_name="user",
        user_agent_kwargs={"model": models["user"]},
        assistant_role_name="Information_retriever",
        assistant_agent_kwargs={"model": models["assistant"], "tools": tools},
    )

    return society


def analyze_chat_history(chat_history: list[dict]) -> None:
    """Extract and logger.info every URL that the agents actually browsed."""
    queried_urls: list[str] = []
    for turn in chat_history:
        for call in turn.get("tool_calls", []):
            if call.get("tool_name") == "browse_url":
                url = call.get("args", {}).get("start_url")
                if url:
                    queried_urls.append(url)

    logger.info("\n============ URL Analysis ============")

    logger.info(f"Total queried URLs: {len(queried_urls)}")
    for url in queried_urls:
        logger.info(url)
    with open("process_history.json", "w", encoding="utf-8") as fp:
        json.dump(chat_history, fp, ensure_ascii=False, indent=2)
    logger.info("Records saved to process_history.json")
    logger.info("============ Analysis Complete ============\n")


# ------------------ Pydantic Schemas ------------------

class PersonalInformation(BaseModel):
    name: str
    positions: list[str]
    contact_information: str | None = None
    social_media: list[str] | None = None
    research_keywords: list[str]


class Biography(BaseModel):
    career_history: str
    research_focus: str


class ResearchInterests(BaseModel):
    areas: list[str]


class AwardsAndDistinctions(BaseModel):
    honors: list[str]


class Education(BaseModel):
    degrees: list[str]


class ScholarProfile(BaseModel):
    personal_information: PersonalInformation
    biography: Biography
    research_interests: ResearchInterests
    awards_and_distinctions: AwardsAndDistinctions
    education: Education


def generate_html_profile(input_text: str,
                          output_file: str = "profile.html") -> None:
    """Pipeline: extract structured profile from a free‑form biography and
    turn it into a polished HTML page.

    Parameters
    ----------
    input_text : str
        Raw biography or resume text.
    output_file : str, optional
        Path where the final HTML file will be saved, by default
        "profile.html".
    """
    extraction_prompt = (
        "You are a scholarly‑profile extraction assistant. "
        "Return ONLY JSON that matches the provided schema."
    )

    extractor = ChatAgent(system_message=extraction_prompt)
    extraction_response = extractor.step(
        input_message=input_text,
        response_format=ScholarProfile,
    )
    profile: ScholarProfile = extraction_response.msgs[0].parsed

    html_system_prompt = "You are an expert HTML profile page generator."
    html_agent = ChatAgent(system_message=html_system_prompt)

    html_user_prompt = f"""
    Using the following JSON, build a complete HTML5 profile page.

    • Sections: Personal Information, Biography, Research Interests, Awards 
    and Distinctions, Education.
    Generate a professional and natural-looking personal profile HTML page based 
    on the provided information, following these detailed requirements:
    Use standard HTML5 structure.
    Layout should be clearly organized using <h1> for the main title, <h2> for 
    section headings, and <p> for paragraph text.
    Use proper <a href> hyperlinks for any external links (e.g., LinkedIn, 
    ResearchGate, Google Scholar).
    Write in a natural, flowing narrative style suitable for introducing the 
    person to a broad audience (no bullet points).

    JSON:
    {profile.model_dump_json(indent=2)}
    """

    html_response = html_agent.step(html_user_prompt)
    html_code = html_response.msgs[0].content

    with open(output_file, "w", encoding="utf-8") as fp:
        fp.write(html_code)
    logger.info(f"HTML profile page saved to: {output_file}")


def run_profile_generation(task: str | None = None,
                           html_path: str = "profile.html") -> None:
    """High‑level orchestration: execute the retrieval society, analyse
    the browsing history, and render the final HTML profile.
    """
    default_task = (
        "find Bernard‑Ghanem's information based on these websites:\n"
        "https://www.linkedin.com/in/bernardghanem/\n"
        "https://scholar.google.com/citations?hl=en&user=rVsGTeEAAAAJ"
        "&view_op=list_works\n"
        "https://x.com/bernardsghanem\n"
        "https://www.researchgate.net/profile/Bernard-Ghanem\n"

    )
    section_plan = """
    Information summary focus on sections: "
        "Personal Information, Biography, Research Interests, Awards and "
        "Distinctions, Education.
    Each section need to be as detailed as possible.
    """
    task = task or default_task

    society = construct_society(task + section_plan)

    answer, chat_history, token_count = run_society(society, round_limit=9)

    analyze_chat_history(chat_history)

    logger.info("\033[94m===== RAW SUMMARY FROM AGENTS =====\033[0m")
    logger.info(answer)
    logger.info(f"\033[94mToken count: {token_count}\033[0m")

    # turn the raw answer into a polished HTML profile
    generate_html_profile(answer, output_file=html_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate an academic profile page.")
    parser.add_argument("--task", type=str, help="Seed task prompt with URLs.")
    parser.add_argument("--html", type=str, default="profile.html",
                        help="Output HTML file path.")
    args = parser.parse_args()

    run_profile_generation(task=args.task, html_path=args.html)
