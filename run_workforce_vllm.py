from camel.toolkits import (
    SearchToolkit,
    DocumentProcessingToolkit,
    FunctionTool
)
from camel.models import ModelFactory
from camel.types import(
    ModelPlatformType,
    ModelType
)
from camel.tasks import Task
from dotenv import load_dotenv

load_dotenv(override=True)

import os
import json
from typing import List, Dict, Any
from loguru import logger
from utils import OwlWorkforceChatAgent, OwlGaiaWorkforce
from utils.gaia import GAIABenchmark
import shutil
from openai import OpenAI

client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
MODEL_NAME = client.models.list().data[0].id


def construct_agent_list() -> List[Dict[str, Any]]:

    web_model = ModelFactory.create(
        model_platform=ModelPlatformType.VLLM,
        model_type=MODEL_NAME,
        model_config_dict={"temperature": 0},
        url="http://localhost:8000/v1",
        api_key="EMPTY",
    )
    
    document_processing_model = ModelFactory.create(
        model_platform=ModelPlatformType.VLLM,
        model_type=MODEL_NAME,
        model_config_dict={"temperature": 0},
        url="http://localhost:8000/v1",
        api_key="EMPTY",
    )
    
    planning_agent_model = ModelFactory.create(
        model_platform=ModelPlatformType.VLLM,
        model_type=MODEL_NAME,
        model_config_dict={"temperature": 0},
        url="http://localhost:8000/v1",
        api_key="EMPTY",
    )

    search_toolkit = SearchToolkit()
    document_processing_toolkit = DocumentProcessingToolkit(cache_dir="tmp")

    web_agent = OwlWorkforceChatAgent(
"""
You are a helpful assistant that can search the web, extract webpage content, simulate browser actions, and provide relevant information to solve the given task.
Keep in mind that:
- Do not be overly confident in your own knowledge. Searching can provide a broader perspective and help validate existing knowledge.  
- If one way fails to provide an answer, try other ways or methods. The answer does exists.
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
  For example, as for the question "What is the maximum length in meters of #9 in the first National Geographic short on YouTube that was ever released according to the Monterey Bay Aquarium website?", your first search term must be coarse-grained like "National Geographic YouTube" to find the youtube website first, and then try other fine-grained search terms step-by-step to find more urls.
- The results you return do not have to directly answer the original question, you only need to collect relevant information.
""",
        model=web_model,
        tools=[
            FunctionTool(search_toolkit.search_google),
            FunctionTool(search_toolkit.search_wiki),
            FunctionTool(document_processing_toolkit.extract_document_content),
        ]
    )
    
    document_processing_agent = OwlWorkforceChatAgent(
        "You are a helpful assistant that can process documents and multimodal data, such as images, audio, and video.",
        document_processing_model,
        tools=[
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
        "description": "A helpful assistant that can retrieve information from a given website url.",
        "agent": document_processing_agent
    }

    agent_list.append(web_agent_dict)
    agent_list.append(document_processing_agent_dict)
    return agent_list


def construct_workforce() -> OwlGaiaWorkforce:
    
    coordinator_agent_kwargs = {
        "model": ModelFactory.create(
            model_platform=ModelPlatformType.VLLM,
            model_type=MODEL_NAME,
            model_config_dict={"temperature": 0},
            url="http://localhost:8000/v1",
            api_key="EMPTY",
        )
    }
    
    task_agent_kwargs = {
        "model": ModelFactory.create(
            model_platform=ModelPlatformType.VLLM,
            model_type=MODEL_NAME,
            model_config_dict={"temperature": 0},
            url="http://localhost:8000/v1",
            api_key="EMPTY",
        )
    }
    
    answerer_agent_kwargs = {
        "model": ModelFactory.create(
            model_platform=ModelPlatformType.VLLM,
            model_type=MODEL_NAME,
            model_config_dict={"temperature": 0},
            url="http://localhost:8000/v1",
            api_key="EMPTY",
        )
    }
    
    workforce = OwlGaiaWorkforce(
        "Gaia Workforce",
        task_agent_kwargs=task_agent_kwargs,
        coordinator_agent_kwargs=coordinator_agent_kwargs,
        answerer_agent_kwargs=answerer_agent_kwargs
    )

    agent_list = construct_agent_list()
    
    for agent_dict in agent_list:
        workforce.add_single_agent_worker(
            agent_dict["description"],
            worker=agent_dict["agent"],
        )

    return workforce


def process_workforce_task(task_description: str, max_replanning_tries: int = 2) -> str:

    task = Task(content=task_description)
    workforce = construct_workforce()
    processed_task = workforce.process_task(task, max_replanning_tries=max_replanning_tries)
    answer = workforce.get_workforce_final_answer(processed_task)

    return answer


if __name__ == "__main__":
    task_description = "According to the wikipedia, when was The Battle of Diamond Rock took place?"
    answer = process_workforce_task(task_description)
    logger.success(answer)
    
    """
    The Battle of Diamond Rock took place between 31 May and 2 June 1805 during the Napoleonic Wars.
    """

