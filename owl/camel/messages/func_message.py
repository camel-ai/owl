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
from dataclasses import dataclass
from typing import Any, Dict, Optional

from camel.messages import (
    BaseMessage,
    HermesFunctionFormatter,
    OpenAIAssistantMessage,
    OpenAIMessage,
    OpenAIToolMessageParam,
)
from camel.messages.conversion import (
    ShareGPTMessage,
    ToolCall,
    ToolResponse,
)
from camel.messages.conversion.sharegpt.function_call_formatter import (
    FunctionCallFormatter,
)
from camel.types import OpenAIBackendRole


@dataclass
class FunctionCallingMessage(BaseMessage):
    r"""Class for message objects used specifically for
    function-related messages.

    Args:
        func_name (Optional[str]): The name of the function used.
            (default: :obj:`None`)
        args (Optional[Dict]): The dictionary of arguments passed to the
            function. (default: :obj:`None`)
        result (Optional[Any]): The result of function execution.
            (default: :obj:`None`)
        tool_call_id (Optional[str]): The ID of the tool call, if available.
            (default: :obj:`None`)
    """

    func_name: Optional[str] = None
    args: Optional[Dict] = None
    result: Optional[Any] = None
    tool_call_id: Optional[str] = None

    def to_openai_message(
        self,
        role_at_backend: OpenAIBackendRole,
    ) -> OpenAIMessage:
        r"""Converts the message to an :obj:`OpenAIMessage` object.

        Args:
            role_at_backend (OpenAIBackendRole): The role of the message in
                OpenAI chat system.

        Returns:
            OpenAIMessage: The converted :obj:`OpenAIMessage` object.
        """
        if role_at_backend == OpenAIBackendRole.ASSISTANT:
            return self.to_openai_assistant_message()
        elif role_at_backend == OpenAIBackendRole.FUNCTION:
            return self.to_openai_tool_message()
        else:
            raise ValueError(f"Unsupported role: {role_at_backend}.")

    def to_sharegpt(
        self,
        function_format: Optional[FunctionCallFormatter[ToolCall, ToolResponse]] = None,
    ) -> ShareGPTMessage:
        r"""Convert FunctionCallingMessage to ShareGPT message.

        Args:
            function_format (FunctionCallFormatter[ToolCall, ToolResponse],
                optional): The function formatter to use. Defaults to None.
        """

        if function_format is None:
            function_format = HermesFunctionFormatter()
        # The role of the message is an unreliable indicator of whether
        # it is a function call or response, so use result
        if self.result is None:
            # This is a function call
            # TODO: split the incoming types to be more specific
            #  and remove the type ignores
            content = function_format.format_tool_call(
                self.content or "",  # type: ignore[arg-type]
                self.func_name,  # type: ignore[arg-type]
                self.args,  # type: ignore[arg-type]
            )
            return ShareGPTMessage(from_="gpt", value=content)  # type: ignore[call-arg]
        else:
            # This is a function response
            # TODO: Allow for more flexible setting of tool role,
            #  optionally to be the same as assistant messages
            content = function_format.format_tool_response(
                self.func_name,  # type: ignore[arg-type]
                self.result,  # type: ignore[arg-type]
            )
            return ShareGPTMessage(from_="tool", value=content)  # type: ignore[call-arg]

    def to_openai_assistant_message(self) -> OpenAIAssistantMessage:
        r"""Converts the message to an :obj:`OpenAIAssistantMessage` object.

        Returns:
            OpenAIAssistantMessage: The converted :obj:`OpenAIAssistantMessage`
                object.
        """
        if (not self.func_name) or (self.args is None):
            raise ValueError(
                "Invalid request for converting into assistant message"
                " due to missing function name or arguments."
            )

        return {
            "role": "assistant",
            "content": self.content or "",
            "tool_calls": [
                {
                    "id": self.tool_call_id or "null",
                    "type": "function",
                    "function": {
                        "name": self.func_name,
                        "arguments": json.dumps(self.args),
                    },
                }
            ],
        }

    def to_openai_tool_message(self) -> OpenAIToolMessageParam:
        r"""Converts the message to an :obj:`OpenAIToolMessageParam` object
        with the role being "tool".

        Returns:
            OpenAIToolMessageParam: The converted
                :obj:`OpenAIToolMessageParam` object with its role being
                "tool".
        """
        if not self.func_name:
            raise ValueError(
                "Invalid request for converting into function message" " due to missing function name."
            )

        result_content = str(self.result)

        return {
            "role": "tool",
            "content": result_content,
            "tool_call_id": self.tool_call_id or "null",
        }
