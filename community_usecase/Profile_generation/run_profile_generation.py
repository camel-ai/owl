import argparse
import json
import logging
import os
import pathlib
import re
import sys
from typing import Optional

from owl.utils import run_society
from pydantic import BaseModel, Field
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
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False

if not logger.handlers:
    file_handler = logging.FileHandler("process_history.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


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
        # user_data_dir=None,
    )

    tools = [
        *browser_toolkit.get_tools(),
        SearchToolkit().search_exa,
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


def analyze_chat_history(chat_history: list[dict]) -> Optional[str]:
    """Extract and logger.info every URL that the agents actually browsed."""

    final_summary = None

    for item in reversed(chat_history):
        assistant_content = item.get("assistant", "")
        if (
                isinstance(assistant_content, str)
                and "FINAL SUMMARY REPORT" in assistant_content
        ):
            final_summary = assistant_content
    if final_summary:
        logger.info("\033[94m===== RAW SUMMARY FROM AGENTS =====\033[0m")
        logger.info(final_summary)
    else:
        logger.info(
            "\033[91mNo final summary report found in chat history.\033[0m")

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

    return final_summary


# ------------------ Pydantic Schemas ------------------

class PersonalInformation(BaseModel):
    name: str = Field(description="Full name of the scholar")
    positions: list[str] = Field(
        description="List of current academic or professional positions")
    contact_information: Optional[str] = Field(
        description="Primary contact information such as email address"
    )
    social_media: Optional[list[str]] = Field(
        description="List of social media or personal profile URLs (e.g., "
                    "LinkedIn, Twitter)"
    )
    research_keywords: list[str] = Field(
        description="Keywords summarizing key research areas or topics")
    short_introduction: str = Field(
        description="A brief one-paragraph summary of the scholar's profile")


class Biography(BaseModel):
    biography: str = Field(
        description="Narrative biography including career trajectory and "
                    "research journey")


class ResearchInterests(BaseModel):
    areas: str = Field(
        description="Description of his current active or long-term research "
                    "topics")


class AwardsAndDistinctions(BaseModel):
    honors: list[str] = Field(
        description="""List of awards, honors, and professional distinctions 
        received
        Reformat each award as HTML structure, Like:
       <li class="field__item"><strong>The 
       NSF CAREER grant in low-power computing and 
       communication systems</strong>, 2024</li>.
        """
    )


class Education(BaseModel):
    degrees: list[str] = Field(
        description="""
        Academic degrees in reverse chronological order, 
        including institution and year.
        Format each degree in html structure like:
            <dl class="field__item"><dt>Doctor of Philosophy (Ph.D.)</dt>
            <dd class="text-break">Integrated Circuits and Systems, 
            <em>University of California</em>, United States, 2003</dd></dl>
        """)


class Links(BaseModel):
    scholarly_identity_links: list[str] = Field(
        description="""Links to unique scholarly identity profiles (e.g., 
                    ORCID, IEEE Xplore, DBLP)
                    reformat each link in html structure like:
    <li class="field__item"><a class="text-decoration-none" 
    href="https://orcid.org/0000-0003-1849-083X" title="Follow Ahmed Eltawil 
    on ORCID at 0000-0003-1849-083X"><button class="btn btn-orcid px-1 py-0 
    text-bg-light bg-opacity-10 text-break text-wrap" type="button" 
    aria-label="ORCID"><i class="bi bi-orcid mx-1"></i><span class="mx-1 
    text-start">ORCID</span></button></a></li>-->
                    """
    )
    related_sites: list[str] = Field(
        description="""Links to institutional or departmental homepages (e.g., 
                    KAUST ECE department)
    reformat each link in html structure like:
    <li class="list-group-item px-0 field__item"><a class="text-break 
    text-underline-hover" href="https://ece.kaust.edu.sa/" title="Electrical 
    and Computer Engineering (ECE) Academic Program">Electrical and Computer 
    Engineering (ECE)</a></li>
                    """
    )
    related_links: list[str] = Field(
        description="""Links to academic and professional presence (e.g., 
                    Google Scholar, ResearchGate, LinkedIn)
   reformat each link in html structure like:
    <li class="field__item"><a 
    href="https://scholar.google.com/citations?user=XzW-KWoAAAAJ&amp;hl=en" 
    class="text-break text-underline-hover">Publications on Google 
    Scholar</a></li>
                    """
    )


class ScholarProfile(BaseModel):
    personal_information: PersonalInformation
    biography: Biography
    research_interests: ResearchInterests
    awards_and_distinctions: AwardsAndDistinctions
    education: Education
    links: Links


def generate_html_profile(input_text,
                          template_path: str = "template.html",
                          output_file: str =
                          "profile_without_url_provided.html",
                          base_url: str = "https://cemse.kaust.edu.sa") -> \
        None:
    """Fill an HTML template with profile data, some with agent rewriting,
    and write to file."""
    extraction_prompt = (
        "You are a scholarly‑profile extraction assistant. "
        "Return ONLY JSON that matches the provided schema."
    )

    extractor = ChatAgent(system_message=extraction_prompt)
    extraction_response = extractor.step(
        input_message=input_text,
        response_format=ScholarProfile,
    )
    profile = extraction_response.msgs[0].parsed

    def to_html_list(items: list[str]) -> str:
        return "<br>".join(items)

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    name = profile.personal_information.name
    slug = name.replace(" ", '-').lower()
    share_url = f"{base_url}/profiles/{slug}"

    filled = (
        template
        .replace("{{ name }}", name)
        .replace("{{ personal information }}",
                 to_html_list(profile.personal_information.positions))
        .replace("{{ email }}",
                 profile.personal_information.contact_information)
        .replace("{{ introduction }}",
                 profile.personal_information.short_introduction)
        .replace("{{ biography }}", profile.biography.biography)
        .replace("{{ research interests }}",
                 profile.research_interests.areas)
        .replace("{{ awards and distinctions }}",
                 to_html_list(profile.awards_and_distinctions.honors))
        .replace("{{ education }}",
                 to_html_list(profile.education.degrees))
        .replace("{{ engage }}",
                 to_html_list(profile.links.scholarly_identity_links))
        .replace("{{ related sites }}",
                 to_html_list(profile.links.related_sites))
        .replace("{{ related links }}",
                 to_html_list(profile.links.related_links))
        .replace("{{ slug }}", slug)
        .replace("{{ base_url }}", base_url)
        .replace("{{ share_url }}", share_url)
        .replace("{{ summary }}",
                 profile.personal_information.short_introduction.replace('\n',
                                                                         '%0A'))
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(filled)

    logger.info(f"HTML profile generated at: {output_file}")


def run_profile_generation(task: str | None = None,
                           white_list=None,
                           black_list=None) -> None:
    """High‑level orchestration: execute the retrieval society, analyse
    the browsing history, and render the final HTML profile.
    """
    if white_list is None:
        white_list = []
    if black_list is None:
        black_list = []

    default_task = (
        """find Bernard‑Ghanem's information based on information you 
        searched in internet
        """
    )

    # Dynamically add white/blacklist instructions
    list_instructions = ""
    if white_list:
        white_sites = ', '.join(white_list)
        list_instructions += (f"\nPlease only retrieve or browse information "
                              f"from the following websites: {white_sites}.\n")
    if black_list:
        black_sites = ', '.join(black_list)
        list_instructions += (f"\nPlease do not browse or retrieve any "
                              f"information from the following websites: "
                              f"{black_sites}.\n")

    section_plan = """
    If there is no URLs provided, please first search websites and then 
    browse them to get relevant information.

    Information summary focus on sections: 
        Personal Information, Biography, Research Interests, Awards and 
        Distinctions (Complete list of honors and corresponding years, 
        honors could be best paper or something else significant), 
        Education (Complete education history and corresponding years), 
        Related Links (Links to institutional or departmental homepages 
        (e.g., xxx department)), 
        Related Sites (Links to professional profiles  
        (e.g., Google Scholar, ResearchGate, LinkedIn)), 
        Scholarly Identity Links (Links to unique scholarly identity profiles 
        (e.g., ORCID, IEEE Xplore, DBLP))

    DO NOT OMIT information in the summary.
    Each section needs to be as detailed as possible.

    Final summary report please note "FINAL SUMMARY REPORT" at the beginning.
    """

    task = (task or default_task) + list_instructions + section_plan

    society = construct_society(task)

    answer, chat_history, token_count = run_society(society, round_limit=9)

    final_summary = analyze_chat_history(chat_history)

    logger.info(f"\033[94mToken count: {token_count}\033[0m")

    # Turn the raw answer into a polished HTML profile
    generate_html_profile(final_summary, output_file='profile.html')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate an academic profile page.")
    parser.add_argument("--task", type=str, help="Seed task prompt")
    parser.add_argument("--whitelist", nargs='+', default=[],
                        help="List of websites recommend to browse")
    parser.add_argument("--blacklist", nargs='+', default=[],
                        help="List of websites not allowed to browse")

    args = parser.parse_args()
    run_profile_generation(task=args.task, white_list=args.whitelist,
                           black_list=args.blacklist)
