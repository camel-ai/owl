# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You can obtain a copy of the License at
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
Workforce example using DeepSeek models.

To run this file, you need to configure the DeepSeek API key.
You can obtain your API key from DeepSeek platform: https://platform.deepseek.com/api_keys
Set it as DEEPSEEK_API_KEY="your-api-key" in your .env file or add it to your environment variables.
"""

import sys
import pathlib
from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.agents import ChatAgent
from camel.toolkits import (
    FunctionTool,
    CodeExecutionToolkit,
    ExcelToolkit,
    SearchToolkit,
    FileToolkit,
)
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level
from camel.tasks.task import Task

from camel.societies import Workforce

from owl.utils import DocumentProcessingToolkit

from typing import List, Dict, Any

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")


def construct_agent_list() -> List[Dict[str, Any]]:
    """Construct a list of agents with their configurations."""
    
    web_model = ModelFactory.create(
        model_platform=ModelPlatformType.DEEPSEEK,
        model_type=ModelType.DEEPSEEK_CHAT,
        model_config_dict={"temperature": 0},
    )
    
    document_processing_model = ModelFactory.create(
        model_platform=ModelPlatformType.DEEPSEEK,
        model_type=ModelType.DEEPSEEK_CHAT,
        model_config_dict={"temperature": 0},
    )
    
    reasoning_model = ModelFactory.create(
        model_platform=ModelPlatformType.DEEPSEEK,
        model_type=ModelType.DEEPSEEK_CHAT,
        model_config_dict={"temperature": 0},
    )

    search_toolkit = SearchToolkit()
    document_processing_toolkit = DocumentProcessingToolkit(model=document_processing_model)
    code_runner_toolkit = CodeExecutionToolkit(sandbox="subprocess", verbose=True)
    file_toolkit = FileToolkit()
    excel_toolkit = ExcelToolkit()

    web_agent = ChatAgent(
        """You are a helpful assistant that can search the web, extract webpage content, and provide relevant information to solve the given task.
Keep in mind that:
- Do not be overly confident in your own knowledge. Searching can provide a broader perspective and help validate existing knowledge.
- If one way fails to provide an answer, try other ways or methods. The answer does exist.
- When looking for specific numerical values (e.g., dollar amounts), prioritize reliable sources.
- When solving tasks that require web searches, check Wikipedia first before exploring other websites.
- In your response, you should mention the urls you have visited and processed.

Here are some tips that help you perform web search:
- Never add too many keywords in your search query!
- If the question is complex, search results typically do not provide precise answers. The search query should be concise and focuses on finding official sources rather than direct answers.
- The results you return do not have to directly answer the original question, you only need to collect relevant information.
""",
        model=web_model,
        tools=[
            FunctionTool(search_toolkit.search_duckduckgo),
            FunctionTool(search_toolkit.search_wiki),
            FunctionTool(search_toolkit.search_baidu),
            FunctionTool(document_processing_toolkit.extract_document_content),
        ]
    )
    
    document_processing_agent = ChatAgent(
        "You are a helpful assistant that can process documents and multimodal data, and can interact with file system.",
        document_processing_model,
        tools=[
            FunctionTool(document_processing_toolkit.extract_document_content),
            FunctionTool(code_runner_toolkit.execute_code),
            *file_toolkit.get_tools(),
        ]
    )
    
    reasoning_coding_agent = ChatAgent(
        "You are a helpful assistant that specializes in reasoning and coding, and can think step by step to solve the task. When necessary, you can write python code to solve the task. If you have written code, do not forget to execute the code. Never generate codes like 'example code', your code should be able to fully solve the task. You can also leverage multiple libraries, such as requests, BeautifulSoup, re, pandas, etc, to solve the task. For processing excel files, you should write codes to process them.",
        reasoning_model,
        tools=[
            FunctionTool(code_runner_toolkit.execute_code),
            FunctionTool(excel_toolkit.extract_excel_content),
            FunctionTool(document_processing_toolkit.extract_document_content),
        ]
    )

    agent_list = []
    
    web_agent_dict = {
        "name": "Web Agent",
        "description": "A helpful assistant that can search the web, extract webpage content, and retrieve relevant information.",
        "agent": web_agent
    }
    
    document_processing_agent_dict = {
        "name": "Document Processing Agent",
        "description": "A helpful assistant that can process a variety of local and remote documents, including pdf, docx, images, audio, and video, etc.",
        "agent": document_processing_agent
    }
    
    reasoning_coding_agent_dict = {
        "name": "Reasoning Coding Agent",
        "description": "A helpful assistant that specializes in reasoning, coding, and processing excel files. However, it cannot access the internet to search for information. If the task requires python execution, it should be informed to execute the code after writing it.",
        "agent": reasoning_coding_agent
    }

    agent_list.append(web_agent_dict)
    agent_list.append(document_processing_agent_dict)
    agent_list.append(reasoning_coding_agent_dict)
    return agent_list


def construct_workforce() -> Workforce:
    """Construct a workforce with coordinator and task agents."""
    
    coordinator_agent_kwargs = {
        "model": ModelFactory.create(
            model_platform=ModelPlatformType.DEEPSEEK,
            model_type=ModelType.DEEPSEEK_CHAT,
            model_config_dict={"temperature": 0},
        )
    }
    
    task_agent_kwargs = {
        "model": ModelFactory.create(
            model_platform=ModelPlatformType.DEEPSEEK,
            model_type=ModelType.DEEPSEEK_CHAT,
            model_config_dict={"temperature": 0},
        )
    }
    
    task_agent = ChatAgent(
        "You are a helpful assistant that can decompose tasks and assign tasks to workers.",
        **task_agent_kwargs
    )
    
    coordinator_agent = ChatAgent(
        "You are a helpful assistant that can assign tasks to workers.",
        **coordinator_agent_kwargs
    )
    
    workforce = Workforce(
        "Workforce",
        task_agent=task_agent,
        coordinator_agent=coordinator_agent,
    )

    agent_list = construct_agent_list()
    
    for agent_dict in agent_list:
        workforce.add_single_agent_worker(
            agent_dict["description"],
            worker=agent_dict["agent"],
        )

    return workforce


def main():
    r"""Main function to run the OWL system with an example question."""
    # Default research question
    default_task_prompt = "Search for recent news about the OWL project and generate a report, then save it locally."
    
    # Override default task if command line argument is provided
    task_prompt = sys.argv[1] if len(sys.argv) > 1 else default_task_prompt
    
    task = Task(
        content=task_prompt,
    )
    
    workforce = construct_workforce()

    processed_task = workforce.process_task(task)

    # Output the result
    print(f"\033[94mAnswer: {processed_task.result}\033[0m")


if __name__ == "__main__":
    main()

