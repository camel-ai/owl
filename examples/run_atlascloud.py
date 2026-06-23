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

"""
Workforce example using AtlasCloud's OpenAI-compatible LLM endpoint.

AtlasCloud exposes an OpenAI-compatible chat completions API at:
https://api.atlascloud.ai/v1

Configuration priority:
1. ATLASCLOUD_API_KEY environment variable

Optional environment variables:
- ATLASCLOUD_API_BASE_URL (default: https://api.atlascloud.ai/v1)
- ATLASCLOUD_MODEL_NAME (default: deepseek-ai/DeepSeek-V3-0324)

Run with:
python examples/run_atlascloud.py
python examples/run_atlascloud.py "Your task here"
"""

import os
import sys
import pathlib
from typing import Any, Dict, List

from dotenv import load_dotenv

from camel.agents import ChatAgent
from camel.logger import set_log_level
from camel.models import ModelFactory
from camel.societies import Workforce
from camel.tasks.task import Task
from camel.toolkits import (
    BrowserToolkit,
    CodeExecutionToolkit,
    ExcelToolkit,
    FileToolkit,
    FunctionTool,
    SearchToolkit,
)
from camel.types import ModelPlatformType

from owl.utils import DocumentProcessingToolkit

ATLAS_BASE_URL = "https://api.atlascloud.ai/v1"
ATLAS_MODEL_NAME = "deepseek-ai/DeepSeek-V3-0324"

BASE_DIR = pathlib.Path(__file__).parent.parent
ENV_PATH = BASE_DIR / "owl" / ".env"

load_dotenv(dotenv_path=str(ENV_PATH))
set_log_level(level="DEBUG")


def load_atlascloud_api_key() -> str | None:
    """Load AtlasCloud API key from environment variables."""
    api_key = os.getenv("ATLASCLOUD_API_KEY")
    if api_key:
        return api_key.strip()

    return None


def get_atlascloud_config() -> tuple[str, str, str]:
    """Return AtlasCloud base URL, API key, and model name."""
    api_url = os.getenv("ATLASCLOUD_API_BASE_URL", ATLAS_BASE_URL).strip()
    model_name = os.getenv("ATLASCLOUD_MODEL_NAME", ATLAS_MODEL_NAME).strip()
    api_key = load_atlascloud_api_key()

    if not api_key:
        raise ValueError(
            "Missing AtlasCloud API key. Set ATLASCLOUD_API_KEY in your "
            "environment or owl/.env file."
        )

    return api_url, api_key, model_name


def create_atlas_model():
    """Create an OpenAI-compatible model backed by AtlasCloud."""
    api_url, api_key, model_name = get_atlascloud_config()
    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
        model_type=model_name,
        url=api_url,
        api_key=api_key,
        model_config_dict={"temperature": 0},
    )


def construct_agent_list() -> List[Dict[str, Any]]:
    """Construct a list of agents with AtlasCloud-backed model instances."""
    web_model = create_atlas_model()
    document_processing_model = create_atlas_model()
    reasoning_model = create_atlas_model()
    browsing_model = create_atlas_model()
    planning_model = create_atlas_model()

    search_toolkit = SearchToolkit()
    document_processing_toolkit = DocumentProcessingToolkit(
        model=document_processing_model
    )
    code_runner_toolkit = CodeExecutionToolkit(sandbox="subprocess", verbose=True)
    file_toolkit = FileToolkit()
    excel_toolkit = ExcelToolkit()
    browser_toolkit = BrowserToolkit(
        headless=False,
        web_agent_model=browsing_model,
        planning_agent_model=planning_model,
    )

    web_agent = ChatAgent(
        """You are a helpful assistant that can search the web, extract webpage content, simulate browser actions, and provide relevant information to solve the given task.
Keep in mind that:
- Do not be overly confident in your own knowledge. Searching can provide a broader perspective and help validate existing knowledge.
- If one way fails to provide an answer, try other ways or methods. The answer does exist.
- If the search snippet is unhelpful but the URL comes from an authoritative source, try visit the website for more details.
- When looking for specific numerical values (e.g., dollar amounts), prioritize reliable sources and avoid relying only on search snippets.
- When solving tasks that require web searches, check Wikipedia first before exploring other websites.
- You can also simulate browser actions to get more information or verify the information you have found.
- Browser simulation is also helpful for finding target URLs. Browser simulation operations do not necessarily need to find specific answers, but can also help find web page URLs that contain answers (usually difficult to find through simple web searches). You can find the answer to the question by performing subsequent operations on the URL, such as extracting the content of the webpage.
- Do not solely rely on document tools or browser simulation to find the answer, you should combine document tools and browser simulation to comprehensively process web page information. Some content may need to do browser simulation to get, or some content is rendered by javascript.
- In your response, you should mention the urls you have visited and processed.

Here are some tips that help you perform web search:
- Never add too many keywords in your search query! Some detailed results need to perform browser interaction to get, not using search toolkit.
- If the question is complex, search results typically do not provide precise answers. It is not likely to find the answer directly using search toolkit only, the search query should be concise and focuses on finding official sources rather than direct answers.
- The results you return do not have to directly answer the original question, you only need to collect relevant information.
""",
        model=web_model,
        tools=[
            FunctionTool(search_toolkit.search_duckduckgo),
            FunctionTool(search_toolkit.search_wiki),
            FunctionTool(document_processing_toolkit.extract_document_content),
            *browser_toolkit.get_tools(),
        ],
    )

    document_processing_agent = ChatAgent(
        "You are a helpful assistant that can process documents and multimodal data, and can interact with file system.",
        document_processing_model,
        tools=[
            FunctionTool(document_processing_toolkit.extract_document_content),
            FunctionTool(code_runner_toolkit.execute_code),
            *file_toolkit.get_tools(),
        ],
    )

    reasoning_coding_agent = ChatAgent(
        "You are a helpful assistant that specializes in reasoning and coding, and can think step by step to solve the task. When necessary, you can write python code to solve the task. If you have written code, do not forget to execute the code. Never generate codes like 'example code', your code should be able to fully solve the task. You can also leverage multiple libraries, such as requests, BeautifulSoup, re, pandas, etc, to solve the task. For processing excel files, you should write codes to process them.",
        reasoning_model,
        tools=[
            FunctionTool(code_runner_toolkit.execute_code),
            FunctionTool(excel_toolkit.extract_excel_content),
            FunctionTool(document_processing_toolkit.extract_document_content),
        ],
    )

    return [
        {
            "name": "Web Agent",
            "description": "A helpful assistant that can search the web, extract webpage content, and retrieve relevant information.",
            "agent": web_agent,
        },
        {
            "name": "Document Processing Agent",
            "description": "A helpful assistant that can process a variety of local and remote documents, including pdf, docx, images, audio, and video, etc.",
            "agent": document_processing_agent,
        },
        {
            "name": "Reasoning Coding Agent",
            "description": "A helpful assistant that specializes in reasoning, coding, and processing excel files. However, it cannot access the internet to search for information. If the task requires python execution, it should be informed to execute the code after writing it.",
            "agent": reasoning_coding_agent,
        },
    ]


def construct_workforce() -> Workforce:
    """Construct a workforce with coordinator and task agents."""
    task_agent = ChatAgent(
        "You are a helpful assistant that can decompose tasks and assign tasks to workers.",
        model=create_atlas_model(),
    )
    coordinator_agent = ChatAgent(
        "You are a helpful assistant that can assign tasks to workers.",
        model=create_atlas_model(),
    )

    workforce = Workforce(
        "Workforce",
        task_agent=task_agent,
        coordinator_agent=coordinator_agent,
    )

    for agent_dict in construct_agent_list():
        workforce.add_single_agent_worker(
            agent_dict["description"],
            worker=agent_dict["agent"],
        )

    return workforce


def main():
    r"""Main function to run OWL with AtlasCloud as the provider."""
    default_task_prompt = (
        "Summarize the github stars, fork counts, and recent activity of camel-ai "
        "owl, then save the result as a local markdown file."
    )
    task_prompt = sys.argv[1] if len(sys.argv) > 1 else default_task_prompt

    task = Task(content=task_prompt)
    workforce = construct_workforce()
    processed_task = workforce.process_task(task)
    print(f"\033[94mAnswer: {processed_task.result}\033[0m")


if __name__ == "__main__":
    main()
