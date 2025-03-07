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
from typing import Any, Dict, List, Literal

from pydantic import (
    BaseModel,
    Field,
    RootModel,
    field_validator,
    model_validator,
)


class ShareGPTMessage(BaseModel):
    r"""A single message in ShareGPT format with enhanced validation"""

    from_: Literal["human", "gpt", "system", "tool"] = Field(
        alias="from", description="The role of the message sender"
    )
    value: str = Field(
        min_length=0,
        max_length=100000,
        description="The content of the message",
    )

    model_config = {
        "populate_by_name": True,
        "extra": "forbid",
        "json_schema_extra": {"examples": [{"from": "human", "value": "What's the weather like today?"}]},
    }


class ShareGPTConversation(RootModel):
    r"""A full conversation in ShareGPT format with validation"""

    root: List[ShareGPTMessage]

    @model_validator(mode="after")
    def validate_conversation_flow(self) -> "ShareGPTConversation":
        r"""Validate the conversation follows logical message order"""
        messages = self.root

        if not messages:
            raise ValueError("Conversation cannot be empty")

        if messages[0].from_ not in ("system", "human"):
            raise ValueError("Conversation must start with either system or human message")

        # Validate message sequence
        for i in range(1, len(messages)):
            curr, prev = messages[i], messages[i - 1]

            if curr.from_ == "tool":
                if prev.from_ != "gpt" or "<tool_call>" not in prev.value:
                    raise ValueError(
                        f"Tool response at position {i} " f"must follow an gpt message with a tool call"
                    )

            if curr.from_ == "gpt" and prev.from_ not in (
                "human",
                "tool",
            ):
                raise ValueError(f"Assistant message at position {i} " f"must follow a human or tool message")

        return self

    def model_dump(self, **kwargs):
        return self.root

    def __iter__(self):
        return iter(self.root)


class ToolCall(BaseModel):
    r"""Represents a single tool/function call with validation"""

    name: str = Field(
        min_length=1,
        max_length=256,
        description="The name of the tool to call",
    )
    arguments: Dict[str, Any] = Field(description="The arguments to pass to the tool")

    @field_validator("arguments")
    @classmethod
    def validate_arguments(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        r"""Validate argument structure and content"""

        # Try to serialize arguments to ensure they're JSON-compatible
        try:
            json.dumps(v)
        except (TypeError, ValueError):
            raise ValueError("Arguments must be JSON-serializable")

        return v

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "examples": [
                {
                    "name": "get_weather",
                    "arguments": {"city": "London", "units": "celsius"},
                }
            ]
        },
    }


class ToolResponse(BaseModel):
    r"""Represents a tool/function response with validation. This is a
    base class and default implementation for tool responses, for the purpose
    of converting between different formats.
    """

    name: str = Field(
        min_length=1,
        max_length=256,
        description="The name of the tool that was called",
    )
    content: Any = Field(
        description="The response content from the tool." " Must be JSON serializable literal or object"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        r"""Validate response content structure"""

        # Ensure content is JSON-serializable
        try:
            json.dumps(v)
        except (TypeError, ValueError):
            raise ValueError("Response content must be JSON-serializable")

        return v

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "examples": [
                {
                    "name": "get_weather",
                    "content": {
                        "temperature": 20,
                        "conditions": "sunny",
                        "humidity": 65,
                    },
                }
            ]
        },
    }
