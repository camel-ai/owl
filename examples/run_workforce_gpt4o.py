from camel.toolkits import (
    VideoAnalysisToolkit,
    SearchToolkit,
    CodeExecutionToolkit,
    ImageAnalysisToolkit,
    # DocumentProcessingToolkit, # Not available in camel-ai 0.2.45/0.2.46
    AudioAnalysisToolkit,
    # AsyncBrowserToolkit,  # Not available in camel-ai 0.2.45/0.2.46
    BrowserToolkit,  # Use this instead
    ExcelToolkit,
    FileWriteToolkit,  # Use this instead of DocumentProcessingToolkit
    FunctionTool
)
from camel.models import ModelFactory
from camel.types import(
    ModelPlatformType,
    ModelType
)
from camel.agents import ChatAgent
from camel.configs import ChatGPTConfig
from camel.societies import RolePlaying

from dotenv import load_dotenv

load_dotenv(override=True)

import os
import json
from typing import List, Dict, Any
from loguru import logger

import shutil

# Create a simplified version of the original script that works with standard CAMEL components
def run_camel_agent():
    """
    Run a simplified version of the workforce example using standard CAMEL components
    """
    # Create models
    chat_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O,
        model_config_dict={"temperature": 0},
    )
    
    # Create toolkits
    search_toolkit = SearchToolkit()
    file_write_toolkit = FileWriteToolkit(path="tmp")
    image_analysis_toolkit = ImageAnalysisToolkit(model=chat_model)
    video_analysis_toolkit = VideoAnalysisToolkit(download_directory="tmp/video")
    audio_analysis_toolkit = AudioAnalysisToolkit(cache_dir="tmp/audio", reasoning=True)
    code_runner_toolkit = CodeExecutionToolkit(sandbox="subprocess", verbose=True)
    browser_simulator_toolkit = BrowserToolkit(headless=True, cache_dir="tmp/browser")
    excel_toolkit = ExcelToolkit()
    
    # Create chat agent with tools
    web_tools = [
        FunctionTool(search_toolkit.web_search),
        FunctionTool(file_write_toolkit.read_file),
        FunctionTool(browser_simulator_toolkit.browse_url),
        FunctionTool(video_analysis_toolkit.ask_question_about_video),
    ]
    
    document_tools = [
        FunctionTool(file_write_toolkit.read_file),
        FunctionTool(image_analysis_toolkit.ask_question_about_image),
        FunctionTool(audio_analysis_toolkit.ask_question_about_audio),
        FunctionTool(video_analysis_toolkit.ask_question_about_video),
        FunctionTool(code_runner_toolkit.execute_code),
    ]
    
    coding_tools = [
        FunctionTool(code_runner_toolkit.execute_code),
        FunctionTool(excel_toolkit.extract_excel_content),
        FunctionTool(file_write_toolkit.read_file),
    ]
    
    # Web agent with prompt
    web_agent = ChatAgent(
        model=chat_model,
        system_message="""
You are a helpful assistant that can search the web, extract webpage content, simulate browser actions, and provide relevant information to solve the given task.
Keep in mind that:
- Do not be overly confident in your own knowledge. Searching can provide a broader perspective and help validate existing knowledge.  
- If one way fails to provide an answer, try other ways or methods. The answer does exist.
- If the search snippet is unhelpful but the URL comes from an authoritative source, try visit the website for more details.  
- When looking for specific numerical values (e.g., dollar amounts), prioritize reliable sources and avoid relying only on search snippets.  
- You can also simulate browser actions to get more information or verify the information you have found.
""",
        tools=web_tools
    )
    
    # Example of running an interaction
    logger.info("Starting interaction with web agent")
    response = web_agent.chat("Search for the latest news about artificial intelligence")
    logger.info(f"Web agent response: {response}")
    
    # You can implement more complex interactions here based on your needs

if __name__ == "__main__":
    # Clean up any temporary files
    if os.path.exists("tmp/"):
        shutil.rmtree("tmp/")
    os.makedirs("tmp/", exist_ok=True)
    
    # Run the example
    run_camel_agent()

