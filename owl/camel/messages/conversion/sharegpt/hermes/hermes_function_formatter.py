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
import json
import re
from typing import Any, Dict, List, Optional

from camel.messages.conversion import (
    ToolCall,
    ToolResponse,
)
from camel.messages.conversion.sharegpt.function_call_formatter import (
    FunctionCallFormatter,
)


class HermesToolResponse(ToolResponse):
    r"""Represents a single tool/function call with validation"""

    pass


class HermesToolCall(ToolCall):
    r"""Represents a single tool/function call with validation"""

    pass


class HermesFunctionFormatter(FunctionCallFormatter[HermesToolCall, HermesToolResponse]):
    r"""Hermes-style function calling format implementation with validation"""

    def extract_tool_calls(self, message: str) -> List[HermesToolCall]:
        r"""Extracts all tool calls from the provided message string.

        Args:
            message (str): The input message string containing potential tool
                calls.

        Returns:
            List[HermesToolCall]: A list of parsed HermesToolCall objects.
        """
        tool_calls = []
        pattern = r"<tool_call>\s*({.*?})\s*</tool_call>"
        matches = re.finditer(pattern, message, re.DOTALL)

        for match in matches:
            try:
                call_dict = json.loads(match.group(1).replace("'", '"'))
                tool_calls.append(HermesToolCall.model_validate(call_dict))
            except Exception as e:
                print(f"Warning: Failed to parse tool call: {e}")
                continue

        return tool_calls

    def extract_tool_response(self, message: str) -> Optional[HermesToolResponse]:
        r"""Extracts a single tool response from the provided message string.

        Args:
            message (str): The input message string containing a potential
                tool response.

        Returns:
            Optional[HermesToolResponse]: A parsed HermesToolResponse object,
                or None if no valid response is found.
        """
        pattern = r"<tool_response>\s*({.*?})\s*</tool_response>"
        match = re.search(pattern, message, re.DOTALL)

        if match:
            try:
                response_json = match.group(1)
                response_dict = json.loads(response_json.replace("'", '"'))
                return HermesToolResponse.model_validate(response_dict)
            except Exception as e:
                print(f"Warning: Failed to parse tool response: {e}")
                return None
        return None

    def format_tool_call(self, content: str, func_name: str, args: Dict[str, Any]) -> str:
        r"""Formats a tool call message with the given content, function name,
        and arguments.

        Args:
            content (str): The content or message to be included in the tool
                call.
            func_name (str): The name of the function being called.
            args (Dict[str, Any]): A dictionary of arguments to be passed to
                the function.

        Returns:
            str: A formatted string representing the tool call in Hermes
                format.
        """
        tool_call_dict = {"name": func_name, "arguments": args}
        return f"{content}\n<tool_call>\n{tool_call_dict}\n</tool_call>"

    def format_tool_response(self, func_name: str, result: Any) -> str:
        r"""Formats a tool response message with the given function name and
        result.

        Args:
            func_name (str): The name of the function whose result is being
                returned.
            result (Any): The result to be included in the tool response.

        Returns:
            str: A formatted string representing the tool response in Hermes
                format.
        """
        response_dict = {"name": func_name, "content": result}
        return f"<tool_response>\n{response_dict}\n</tool_response>"
