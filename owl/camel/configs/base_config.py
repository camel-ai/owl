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
from __future__ import annotations

from abc import ABC
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class BaseConfig(ABC, BaseModel):
    r"""Base configuration class for all models.

    This class provides a common interface for all models, ensuring that all
    models have a consistent set of attributes and methods.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
        # UserWarning: conflict with protected namespace "model_"
        protected_namespaces=(),
    )

    tools: Optional[List[Any]] = None
    """A list of tools the model may
    call. Currently, only functions are supported as a tool. Use this
    to provide a list of functions the model may generate JSON inputs
    for. A max of 128 functions are supported.
    """

    @field_validator("tools", mode="before")
    @classmethod
    def fields_type_checking(cls, tools):
        r"""Validate the type of tools in the configuration.

        This method ensures that the tools provided in the configuration are
        instances of `FunctionTool`. If any tool is not an instance of
        `FunctionTool`, it raises a ValueError.
        """
        if tools is not None:
            from camel.toolkits import FunctionTool

            for tool in tools:
                if not isinstance(tool, FunctionTool):
                    raise ValueError(f"The tool {tool} should " "be an instance of `FunctionTool`.")
        return tools

    def as_dict(self) -> dict[str, Any]:
        r"""Convert the current configuration to a dictionary.

        This method converts the current configuration object to a dictionary
        representation, which can be used for serialization or other purposes.

        Returns:
            dict[str, Any]: A dictionary representation of the current
                configuration.
        """
        config_dict = self.model_dump()

        tools_schema = None
        if self.tools:
            from camel.toolkits import FunctionTool

            tools_schema = []
            for tool in self.tools:
                if not isinstance(tool, FunctionTool):
                    raise ValueError(f"The tool {tool} should " "be an instance of `FunctionTool`.")
                tools_schema.append(tool.get_openai_tool_schema())
        config_dict["tools"] = tools_schema
        return config_dict
