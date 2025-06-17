import argparse
import json
import logging
import os
import pathlib
import re
import sys
from typing import List, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from camel.agents import ChatAgent
from camel.logger import get_logger, set_log_level
from camel.models import ModelFactory
from camel.societies import RolePlaying
from camel.toolkits import (
    SearchToolkit,
    BrowserToolkit
)
# from browser_toolkit import BrowserToolkit
from camel.types import ModelPlatformType

# Add Flask imports
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

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
os.environ['EXA_API_KEY'] = "2c73e3b9-7fe9-4c20-aace-b0fb69e18cea"

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication


# 定义返回格式
class WebLinksResponse(BaseModel):
    links: List[str]


def search_web_links(person_info: str, blacklist: List[str]) -> List[str]:
    # 构造黑名单规则字符串
    blacklist_prompt = "\n".join(
        f"- Do NOT include any URLs from '{site}' or any of its subpages."
        for site in blacklist
    )

    # 构造系统提示
    system_message = f"""
    You are a helpful research assistant using the Exa search engine.

    Your goal is to find high-quality links related to a specific scientific 
    employee. These links may include:
    - Their **personal homepage** (usually on a university or personal domain).
    - Their **academic profiles**, such as Google Scholar, ORCID, 
    ResearchGate, Semantic Scholar, etc.
    - Their **social media**, such as X, Linkedin.

    Requirements:
    - Respond in **JSON format**, with this structure:
    {{
      "links": ["https://example.com/page1", "https://example.com/page2"]
    }}
    - Do NOT include any explanation, title, or commentary — only the JSON 
    object.
    - Only include links that directly relate to the professor.
    - Only include working URLs (not summaries).
    {blacklist_prompt}
    """

    # 初始化代理
    agent = ChatAgent(
        system_message=system_message,
        tools=[SearchToolkit().search_exa],
    )

    # 调用 step 生成响应
    response = agent.step(
        input_message=f"Find web links for {person_info}",
        response_format=WebLinksResponse,
    )

    # 提取并返回链接列表（如果解析失败则返回空）
    try:
        return response.msgs[0].parsed.links
    except Exception:
        return []


def run_society(
        society: RolePlaying,
        round_limit: int = 5,
) -> Tuple[str, List[dict], dict]:
    overall_completion_token_count = 0
    overall_prompt_token_count = 0

    chat_history = []
    init_prompt = """
    Now please give me instructions to solve over overall task step by step. 
    If the task requires some specific knowledge, please instruct me to use 
    tools to complete the task.
        """
    input_msg = society.init_chat(init_prompt)
    for _round in range(round_limit):
        assistant_response, user_response = society.step(input_msg)
        # Check if usage info is available before accessing it
        if assistant_response.info.get("usage") and user_response.info.get(
                "usage"):
            overall_completion_token_count += assistant_response.info[
                                                  "usage"].get(
                "completion_tokens", 0
            ) + user_response.info["usage"].get("completion_tokens", 0)
            overall_prompt_token_count += assistant_response.info["usage"].get(
                "prompt_tokens", 0
            ) + user_response.info["usage"].get("prompt_tokens", 0)

        # convert tool call to dict
        tool_call_records: List[dict] = []
        if assistant_response.info.get("tool_calls"):
            for tool_call in assistant_response.info["tool_calls"]:
                tool_call_records.append(tool_call.as_dict())

        _data = {
            "user": user_response.msg.content
            if hasattr(user_response, "msg") and user_response.msg
            else "",
            "assistant": assistant_response.msg.content
            if hasattr(assistant_response, "msg") and assistant_response.msg
            else "",
            "tool_calls": tool_call_records,
        }

        chat_history.append(_data)
        logger.info(
            f"Round #{_round} user_response:\n "
            f"{user_response.msgs[0].content if user_response.msgs and len(user_response.msgs) > 0 else ''}"
        )
        logger.info(
            f"Round #{_round} assistant_response:\n { assistant_response.msgs[0].content if assistant_response.msgs and len(assistant_response.msgs) > 0 else ''}"
        )

        if (
                assistant_response.terminated
                or user_response.terminated
                or "TASK_DONE" in user_response.msg.content
        ):
            break

        input_msg = assistant_response.msg

    answer = chat_history[-1]["assistant"]
    token_info = {
        "completion_token_count": overall_completion_token_count,
        "prompt_token_count": overall_prompt_token_count,
    }

    return answer, chat_history, token_info


def construct_society(task: str) -> Tuple[RolePlaying, BrowserToolkit]:
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
        user_data_dir="./my-user-data-dir",
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

    return society, browser_toolkit


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


class Publications(BaseModel):
    pub_list: list[str] = Field(
        description=""" 
        TOP 10 publication paper list.
        reformat each paper in html structure like:
<dl class="field__item">
  <dt>
    <a href="https://example.com/activitynet" target="_blank">
      ActivityNet: A Large-Scale Video Benchmark for Human Activity 
      Understanding
    </a>
  </dt>
  <dd class="text-break">
    FC Heilbron, V Escorcia, B Ghanem, JC Niebles, 
    <em>IEEE Conference on Computer Vision and Pattern Recognition</em>, 
    2015 (Citations: 3239)
  </dd>
</dl><br>

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
    publications: Publications
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
        if not items:
            return ""
        return "<br>".join(items)

    def safe_str(value) -> str:
        """Safely convert value to string, handling None values."""
        return str(value) if value is not None else ""

    def safe_replace_newlines(text) -> str:
        """Safely replace newlines in text, handling None values."""
        if text is None:
            return ""
        return str(text).replace('\n', '%0A')

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    name = safe_str(profile.personal_information.name)
    slug = name.replace(" ", '-').lower()
    share_url = f"{base_url}/profiles/{slug}"

    filled = (
        template
        .replace("{{ name }}", name)
        .replace("{{ personal information }}",
                 to_html_list(profile.personal_information.positions or []))
        .replace("{{ email }}",
                 safe_str(profile.personal_information.contact_information))
        .replace("{{ introduction }}",
                 safe_str(profile.personal_information.short_introduction))
        .replace("{{ biography }}", safe_str(profile.biography.biography))
        .replace("{{ research interests }}",
                 safe_str(profile.research_interests.areas))
        .replace("{{ awards and distinctions }}",
                 to_html_list(profile.awards_and_distinctions.honors or []))
        .replace("{{ education }}",
                 to_html_list(profile.education.degrees or []))
        .replace("{{ engage }}",
                 to_html_list(profile.links.scholarly_identity_links or []))
        .replace("{{ related sites }}",
                 to_html_list(profile.links.related_sites or []))
        .replace("{{ related links }}",
                 to_html_list(profile.links.related_links or []))
        .replace("{{ publications }}",
                 to_html_list(profile.publications.pub_list or []))
        .replace("{{ slug }}", slug)
        .replace("{{ base_url }}", base_url)
        .replace("{{ share_url }}", share_url)
        .replace("{{ summary }}",
                 safe_replace_newlines(
                     profile.personal_information.short_introduction))
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(filled)

    logger.info(f"HTML profile generated at: {output_file}")


def get_scholar_profile_info(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch the page, status code: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # 获取人名
    name_tag = soup.find('div', id='gsc_prf_in')
    name = name_tag.get_text(strip=True) if name_tag else "Name not found"

    # 获取描述（单位等）
    affiliation_tag = soup.find('div', class_='gsc_prf_il')
    affiliation = affiliation_tag.get_text(
        strip=True) if affiliation_tag else "Affiliation not found"

    return name + ", " + affiliation


def run_profile_generation(task: str | None = None,
                           black_list=None,
                           output_file='profile.html') -> None:
    """High‑level orchestration: execute the retrieval society, analyse
    the browsing history, and render the final HTML profile.
    """

    if black_list is None:
        black_list = []

    default_task = (
        """You need to make a summary for an employee's profile based on 
        given URLs.
        
        """
    )
    person_info = get_scholar_profile_info(task)
    # Dynamically add white/blacklist instructions
    list_instructions = ""
    white_list = search_web_links(person_info=person_info,
                                  blacklist=black_list)

    if white_list:
        white_sites = ', '.join(white_list)
        list_instructions += (f"\nPlease only retrieve or browse information "
                              f"from the following websites: {white_sites}.\n")

    section_plan = """
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
        (e.g., ORCID, IEEE Xplore, DBLP)),
        Representative Publications (The top 10 most cited publications 
        from Google Scholar are listed to highlight the author's impactful 
        research contributions, and links of these papers)

    DO NOT OMIT information in the summary.
    Each section needs to be as detailed as possible.

    Final summary report please note "FINAL SUMMARY REPORT" at the beginning.
    
    NOTICE:  If a Web page has already been visited, do not visit it 
    again regardless of whether the previous attempt was successful or not.
    """

    task = default_task + list_instructions + section_plan

    society, browser_toolkit = construct_society(task)

    try:
        answer, chat_history, token_count = run_society(society, round_limit=1)

        final_summary = analyze_chat_history(chat_history)

        logger.info(f"\033[94mToken count: {token_count}\033[0m")

        # Turn the raw answer into a polished HTML profile
        generate_html_profile(final_summary, output_file=output_file)

    finally:
        # Explicitly close the browser to prevent resource leaks
        try:
            browser_toolkit.close_browser()
            logger.info("Browser closed successfully.")
        except Exception as e:
            logger.warning(f"Could not close browser: {e}")


# Example of reusing BrowserToolkit for multiple sessions:
# browser_toolkit = BrowserToolkit(headless=False, ...)
# try:
#     result1 = browser_toolkit.browse_url("task1", "url1")
#     result2 = browser_toolkit.browse_url("task2", "url2")  # Reuses same
#     browser
# finally:
#     browser_toolkit.close_browser()  # Close when done

# Flask API Endpoints

@app.route('/api/search_scholar', methods=['POST'])
def api_search_scholar():
    """API endpoint to get scholar info and white list from Google Scholar
    URL."""
    try:
        data = request.get_json()
        scholar_url = data.get('scholar_url')
        blacklist = data.get('blacklist', [])

        if not scholar_url:
            return jsonify({'error': 'Scholar URL is required'}), 400

        # Get scholar information
        person_info = get_scholar_profile_info(scholar_url)

        # Get white list
        white_list = search_web_links(person_info=person_info,
                                      blacklist=blacklist)

        return jsonify({
            'person_info': person_info,
            'white_list': white_list,
            'status': 'success'
        })

    except Exception as e:
        logger.error(f"Error in search_scholar: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate_profile', methods=['POST'])
def api_generate_profile():
    """API endpoint to generate profile with confirmed white list."""
    try:
        data = request.get_json()
        scholar_url = data.get('scholar_url')
        blacklist = data.get('blacklist', [])
        white_list = data.get('white_list', [])

        if not scholar_url or not white_list:
            return jsonify(
                {'error': 'Scholar URL and white list are required'}), 400

        # Run profile generation with confirmed white list
        person_info = get_scholar_profile_info(scholar_url)

        default_task = (
            """You need to make a summary for an employee's profile based on 
            given URLs.
            """
        )

        # Use the confirmed white list
        list_instructions = ""
        if white_list:
            white_sites = ', '.join(white_list)
            list_instructions += (
                f"\nPlease only retrieve or browse information "
                f"from the following websites: {white_sites}.\n")
        if blacklist:
            black_sites = ', '.join(blacklist)
            list_instructions += (f"\nPlease do not browse or retrieve any "
                                  f"information from the following websites: "
                                  f"{black_sites}.\n")
        section_plan = """
        
        Information summary focus on sections: 
            Personal Information, Biography, Research Interests, 
            Email address, Awards and 
            Distinctions (Complete list of honors and corresponding years, 
            honors could be best paper or something else significant), 
            Education (Complete education history and corresponding years), 
            Related Links (Links to institutional or departmental homepages 
            (e.g., xxx department)), 
            Related Sites (Links to professional profiles  
            (e.g., Google Scholar, ResearchGate, LinkedIn)), 
            Scholarly Identity Links (Links to unique scholarly identity 
            profiles 
            (e.g., ORCID, IEEE Xplore...)),
            Representative Publications (The top 10 most cited publications 
            from Google Scholar, Paper name and citation numbers.)
            
        All of the above information must be clearly presented with full details in the FINAL SUMMARY REPORT.
        DO NOT OMIT information in the summary.
        Each section needs to be as detailed as possible.

        Final summary report please note "FINAL SUMMARY REPORT" at the 
        beginning.
        
        
        """

        task = default_task + list_instructions + section_plan
        society, browser_toolkit = construct_society(task)

        try:
            answer, chat_history, token_count = run_society(society,
                                                            round_limit=1)
            final_summary = analyze_chat_history(chat_history)

            # Generate HTML profile
            output_file = 'scholar.html'
            generate_html_profile(final_summary, output_file=output_file)

            return jsonify({
                'status': 'success',
                'message': 'Profile generated successfully',
                'token_count': token_count,
                'output_file': output_file
            })

        finally:
            # Explicitly close the browser to prevent resource leaks
            try:
                browser_toolkit.close_browser()
                logger.info("Browser closed successfully.")
            except Exception as e:
                logger.warning(f"Could not close browser: {e}")

    except Exception as e:
        logger.error(f"Error in generate_profile: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_profile', methods=['GET'])
def api_get_profile():
    """API endpoint to serve the generated HTML profile."""
    try:
        profile_path = 'scholar.html'
        if os.path.exists(profile_path):
            return send_file(profile_path, as_attachment=False)
        else:
            return jsonify({'error': 'Profile not found'}), 404
    except Exception as e:
        logger.error(f"Error serving profile: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/')
def serve_frontend():
    """Serve the frontend HTML."""
    return send_file('templates/index.html')


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate an academic profile page.")
    parser.add_argument("--task", type=str, help="Seed task prompt")
    parser.add_argument("--output_file", type=str, help="html page file name")
    parser.add_argument("--whitelist", nargs='+', default=[],
                        help="List of websites recommend to browse")
    parser.add_argument("--blacklist", nargs='+', default=[],
                        help="List of websites not allowed to browse")
    parser.add_argument("--web", action='store_true', help="Run as web server")

    args = parser.parse_args()

    if args.web:
        # Start Flask development server
        print("Starting Profile Generation Web Server...")
        print("Open your browser and go to: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        # Original command line functionality
        if args.task:
            run_profile_generation(task=args.task,
                                   black_list=args.blacklist,
                                   output_file=args.output_file)
        else:
            # Default execution for testing
            people_name = ('https://scholar.google.com/citations?user'
                           '=rVsGTeEAAAAJ')
            run_profile_generation(people_name,
                                   black_list=['http://kaust.edu.sa/'],
                                   output_file='scholar.html')
