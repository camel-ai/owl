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
import asyncio
import logging
import os
from typing import List, Tuple, Optional, Union, Any, Callable
from pydantic import BaseModel, Field
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.toolkits import HybridBrowserToolkit, FileWriteToolkit, \
    SearchToolkit, FunctionTool
from camel.types import ModelPlatformType, ModelType
import requests
from bs4 import BeautifulSoup
import argparse
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import shutil
import uuid
import threading

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('browser_dom_debug.log'),  # File output
    ],
)

logging.getLogger('camel.agents').setLevel(logging.INFO)
logging.getLogger('camel.models').setLevel(logging.INFO)
logging.getLogger('camel.toolkits').setLevel(logging.INFO)
# logging.getLogger('camel.toolkits.HybridBrowserToolkit').setLevel(
#     logging.DEBUG)

USER_DATA_DIR = r"D:/User_Data"


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
      ActivityNet: A Large-Scale Video Benchmark for Human Activity 
      Understanding
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
    - Their **social media**, such as X (twitter), Linkedin.

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
        parsed_result = response.msgs[0].parsed
        if isinstance(parsed_result, WebLinksResponse):
            return parsed_result.links
        else:
            return []
    except Exception:
        return []


def generate_html_profile(input_text,
                          template_path: str = "template.html",
                          output_file: str =
                          "profile.html",
                          base_url: str = "https://cemse.kaust.edu.sa") -> \
        None:
    """Fill an HTML template with profile data, some with agent rewriting,
    and write to file."""
    extraction_prompt = (
        "You are a scholarly‑profile extraction assistant. "
        "Return ONLY JSON that matches the provided schema."
        "Please do not output vague terms like 'unspecified' or 'likely'"
        ". Even if information is missing, do not use vague words."
    )

    extractor = ChatAgent(system_message=extraction_prompt)
    extraction_response = extractor.step(
        input_message=input_text,
        response_format=ScholarProfile,
    )
    profile = extraction_response.msgs[0].parsed

    # Ensure profile is of correct type
    if not isinstance(profile, ScholarProfile):
        raise ValueError("Failed to parse scholar profile from response")

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


model_backend = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4_1,
    model_config_dict={"temperature": 0.0, "top_p": 1},
)

# Set up output directory
output_dir = "./file_write_outputs"
os.makedirs(output_dir, exist_ok=True)

# Initialize the FileWriteToolkit with the output directory
file_toolkit = FileWriteToolkit(output_dir=output_dir)

TASK_PROMPT = """

> Please extract and compile detailed academic and professional information 
from the provided webpages. Extract different types of information and save 
them into separate Markdown files according to the specified categories.
>
> ### Information Categories and File Names:
>
> 1. **Personal Information** → Save to: `personal_information.md`
>    * Full name
>    * Current position(s)
>    * Institutional affiliation(s)
>    * Contact details (e.g., email, office address, phone number)
>    * Social media profiles and personal URLs
>
> 2. **Biography** → Save to: `biography.md`
>    * A concise narrative summary highlighting academic background, career 
development, and major milestones
>
> 3. **Research Interests** → Save to: `research_interests.md`
>    * Main research areas and topics of focus, both theoretical and applied
>    * Research keywords and specializations
>
> 4. **Awards and Distinctions** → Save to: `awards_distinctions.md`
>    * A complete chronological list of honors and recognitions (e.g., 
best paper awards, fellowships, keynote speeches, society memberships)
>    * Include the full title of each award, the granting organization, 
and the year received
>
> 5. **Education** → Save to: `education.md`
>    * Full academic history including degree(s) earned, field(s) of study, 
institutions, thesis titles (if available), and years of graduation
>
> 6. **Publications** → Save to: `publications.md`
>    * From Google Scholar (if accessible), list the **top 10 most cited 
publications**
>    * For each publication, include: Title, Authors, Venue and year, 
Citation count
>
> 7. **Professional Links** → Save to: `professional_links.md`
>    * Related Links: Links to institutional or departmental pages (e.g., 
university faculty page, lab homepage)
>    * Related Sites: Links to professional profiles (e.g., Google Scholar, 
ResearchGate, LinkedIn, Semantic Scholar)
>    * Scholarly Identity Links: Unique identifiers from academic databases 
(e.g., ORCID, DBLP, IEEE Xplore, Scopus Author ID, Web of Science ResearcherID)
>    * PLEASE not generate fake links, If you don't find the corresponding 
link, then don't include it.
> ### Instructions:
>
> * For each category, create a separate .md file using the write_to_file 
function
> * Use clear section headings with Markdown syntax (`##`)
> * Use bullet points or tables where appropriate for clarity
> * Only create files for categories where data is actually found on the 
webpages
> * Do not create empty files - only save files that contain actual information

You need to interact with each webpage, clicking to obtain useful information.
For example, if you see a 'DBLP' link tag on the page like '- link "DBLP" [
ref=e105]',
 you should use the get_page_links tool to obtain the accurate DBLP page URL.
get_page_links can only process element with 'link' tag!
When you call a tool, all operations will only take place on the current page.
 If you visit another page,
  you can no longer input the reference from a previous page into the tool.
"""


def aggregate_markdown_files(directory: str) -> str:
    """Read all markdown files in *directory* and concatenate them into one
    string.

    The individual file contents are separated by two newlines and prefixed
    with a markdown header indicating the file name so that downstream
    processing can still recover file-level boundaries if needed.
    """
    contents: List[str] = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(".md"):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                contents.append(f"# {filename}\n\n" + file_content)
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
    return "\n\n".join(contents)


# -------------------- Pipeline (Async) --------------------

async def run_pipeline(start_url: str,
                       blacklist: Optional[List[str]] = None,
                       links: Optional[List[str]] = None,
                       progress_cb: Optional[
                           Callable[[int], None]] = None) -> str:
    """End-to-end pipeline to fetch scholar profile, crawl links and
    generate HTML.

    Args:
        start_url: The Google Scholar (or similar) profile URL.
        blacklist: Optional list of domains that should be excluded when
            searching links.
        links: Optional list of links to be used instead of searching for
        new ones.
    """
    blacklist = blacklist or []

    # Prepare output directory (clean slate each run)
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            logger.warning(f"Could not clean output_dir: {e}")
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Extract brief personal information from the scholar profile page
    person_info = get_scholar_profile_info(start_url)
    logger.info(f"Extracted person info: {person_info}")

    # Step 2: Retrieve relevant links unless provided explicitly
    links = links or search_web_links(person_info, blacklist)
    logger.info(f"Using {len(links)} links: {links}")

    # Step 3: Process all links synchronously with a single agent

    # Create links text for the prompt
    links_text = "\n".join([f"- {link}" for link in links])

    # Single prompt with all links
    prompt = f"""Target links to process:
{links_text}

Please process all the above links and extract the information specified in 
the system message. 
For each type of information found across all the websites, create a separate 
.md file using the write_to_file function.
Use the exact file names specified in the system message (e.g., 
personal_information.md, biography.md, research_interests.md, etc.).
Aggregate information of the same type from all links into the same file.

DO NOT generate fake links in markdown file.
"""

    logger.info(f"Processing {len(links)} links synchronously")
    custom_tools = [
        "open_browser",
        "close_browser",
        "visit_page",
        "click",
        "type",
        "get_page_links",
    ]

    toolkit = HybridBrowserToolkit(headless=False,
                                   user_data_dir=USER_DATA_DIR,
                                   enabled_tools=custom_tools)
    file_tool = FileWriteToolkit(output_dir=output_dir)
    agent = ChatAgent(
        system_message=TASK_PROMPT,
        model=model_backend,
        tools=[*toolkit.get_tools(), *file_tool.get_tools()],
        max_iteration=20,
        # Increased iteration limit for processing multiple links
    )

    try:
        await agent.astep(prompt)

        # progress increment - step 1: processing all links completed
        if progress_cb:
            progress_cb(1)
    finally:
        # Ensure browser session closes
        try:
            await toolkit.close_browser()
        except Exception:
            pass

    # Step 4: Aggregate all generated markdown files into one text block
    aggregated_markdown = aggregate_markdown_files(output_dir)
    if not aggregated_markdown:
        logger.warning(
            "No markdown content collected – skipping HTML generation.")
        return ""

    # Step 5: Feed the aggregated content to the profile HTML generator
    output_html = "profile.html"
    generate_html_profile(aggregated_markdown, output_file=output_html)

    if progress_cb:
        progress_cb(1)  # step 2: html generation completed

    return os.path.abspath(output_html)


# -------------------- Progress Tracking --------------------

class _ProgressRecord:
    __slots__ = ("total", "current", "done", "output_file")

    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.done = False
        self.output_file: Optional[str] = None

    def inc(self, n: int = 1):
        self.current += n


_PROGRESS_STORE: dict[str, "_ProgressRecord"] = {}


def _start_background_pipeline(job_id: str, scholar_url: str,
                               blacklist: List[str], links: List[str]):
    """Run pipeline in background thread and update progress store."""

    async def _run():
        record = _PROGRESS_STORE[job_id]

        def _callback(step: int = 1):
            record.inc(step)

        try:
            output_path = await run_pipeline(
                scholar_url,
                blacklist,
                links,
                progress_cb=_callback,
            )
            record.output_file = output_path
        finally:
            record.done = True

    asyncio.run(_run())


# -------------------- Flask Backend --------------------

app = Flask(__name__, static_folder="templates", template_folder="templates")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def index_page():
    """Serve the front-end HTML page."""
    return send_file(os.path.join(BASE_DIR, "templates", "index.html"))


@app.route("/api/search_scholar", methods=["POST"])
def api_search_scholar():
    data: dict[str, Any] = request.get_json(force=True)
    scholar_url: str = data.get("scholar_url", "")
    blacklist: List[str] = data.get("blacklist", [])

    if not scholar_url:
        return jsonify(
            {"status": "error", "error": "Missing 'scholar_url'"}), 400

    try:
        person_info = get_scholar_profile_info(scholar_url)
        links = search_web_links(person_info, blacklist)
        return jsonify({
            "status": "success",
            "person_info": person_info,
            "white_list": links,
        })
    except Exception as exc:
        logger.exception("Search scholar failed")
        return jsonify({"status": "error", "error": str(exc)}), 500


@app.route("/api/generate_profile", methods=["POST"])
def api_generate_profile():
    data: dict[str, Any] = request.get_json(force=True)
    scholar_url: str = data.get("scholar_url", "")
    blacklist: List[str] = data.get("blacklist", [])
    white_list: List[str] = data.get("white_list", [])

    if not scholar_url:
        return jsonify(
            {"status": "error", "error": "Missing 'scholar_url'"}), 400

    # Launch background job for progress tracking
    job_id = str(uuid.uuid4())
    total_steps = 2  # 1 for processing all links + 1 for HTML gen
    _PROGRESS_STORE[job_id] = _ProgressRecord(total_steps)

    thread = threading.Thread(target=_start_background_pipeline, args=(
        job_id, scholar_url, blacklist, white_list), daemon=True)
    thread.start()

    return jsonify(
        {"status": "accepted", "job_id": job_id, "total": total_steps})


@app.route('/api/progress/<job_id>')
def api_progress(job_id: str):
    record = _PROGRESS_STORE.get(job_id)
    if record is None:
        return jsonify({"status": "error", "error": "invalid job id"}), 404
    return jsonify({
        "status": "success",
        "current": record.current,
        "total": record.total,
        "done": record.done,
        "output_file": record.output_file,
    })


@app.route('/files/<path:filename>')
def serve_generated_file(filename: str):
    """Serve generated HTML/markdown files so that the browser can open
    them."""
    return send_from_directory(BASE_DIR, filename, as_attachment=False)


@app.route("/api/add_account_info", methods=["POST"])
def api_add_account_info():
    """Launch a persistent Playwright browser so that user can log in manually.

    The browser is started in a detached background thread so that the Flask
    request thread returns immediately. The browser session will reuse the
    global USER_DATA_DIR to preserve cookies / login state for subsequent
    automated crawling tasks.
    """

    def _open_browser():
        try:
            from playwright.sync_api import sync_playwright
            _p = sync_playwright().start()
            context = _p.chromium.launch_persistent_context(
                USER_DATA_DIR,
                headless=False,
                args=["--start-maximized"],
            )

            # Wait until the browser context itself is closed by the user.
            # This will keep the thread alive and prevent the window from
            # disappearing immediately.
            try:
                context.wait_for_event("close", timeout=0)
            finally:
                try:
                    context.close()
                except Exception:
                    pass  # context may already be closed
                _p.stop()
        except Exception as exc:
            logger.exception(
                "Failed to open Playwright persistent context: %s", exc)

    threading.Thread(target=_open_browser, daemon=True).start()
    return jsonify({"status": "success"})


def _main_cli():
    args = _parse_args()
    # If user specifies URL via CLI, just run once as before
    asyncio.run(run_pipeline(args.url, args.blacklist))


if __name__ == "__main__":
    import sys

    if "--url" in sys.argv or len(sys.argv) > 1:
        # CLI mode
        _main_cli()
    else:
        # Run Flask server
        app.run(host="0.0.0.0", port=5000, debug=False)


# -------------------- CLI Entry Point --------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an HTML scholar profile from a starting URL.")
    parser.add_argument(
        "--url",
        default="https://scholar.google.com/citations?user=rVsGTeEAAAAJ",
        help="The scholar profile URL to start from."
    )
    parser.add_argument(
        "--blacklist",
        nargs="*",
        default=[],
        help="Domains to exclude when searching for links."
    )
    return parser.parse_args()
