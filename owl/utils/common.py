import sys

sys.path.append("../")

import json
import re
from typing import Dict, Optional, List
from loguru import logger

from camel.toolkits import *


def extract_pattern(content: str, pattern: str) -> Optional[str]:
    try:
        _pattern = rf"<{pattern}>(.*?)</{pattern}>"
        match = re.search(_pattern, content, re.DOTALL)
        if match:
            text = match.group(1)
            return text.strip()
        else:
            return None
    except Exception as e:
        logger.warning(f"Error extracting answer: {e}, current content: {content}")
        return None


def extract_dict_from_str(text: str) -> Optional[Dict]:
    r"""Extract dict from LLM's outputs including "```json ```" tag."""
    text = text.replace("\\", "")
    pattern = r"```json\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        try:
            # Parse the JSON string into a dictionary
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    return None


def process_tools(tools: List[str] | str) -> List[FunctionTool]:
    r"""Process the tools from the configuration."""
    tool_list = []
    if isinstance(tools, str):
        tools = [tools]
    for tool_name in tools:
        if tool_name in globals():
            toolkit_class: BaseToolkit = globals()[tool_name]
            if tool_name == "CodeExecutionToolkit":
                tool_list.extend(toolkit_class(sandbox="subprocess", verbose=True).get_tools())
            elif tool_name == "ImageAnalysisToolkit":
                tool_list.extend(toolkit_class(model="gpt-4o").get_tools())
            elif tool_name == "AudioAnalysisToolkit":
                tool_list.extend(toolkit_class(reasoning=True).get_tools())
            elif tool_name == "WebToolkit":
                tool_list.extend(toolkit_class(headless=True).get_tools())
            else:
                tool_list.extend(toolkit_class().get_tools())

        else:
            raise ValueError(f"Toolkit {tool_name} not found.")

    return tool_list
