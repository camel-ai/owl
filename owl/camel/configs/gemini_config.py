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

from typing import Any, Optional, Sequence, Type, Union

from pydantic import BaseModel

from camel.configs.base_config import BaseConfig
from camel.types import NOT_GIVEN, NotGiven


class GeminiConfig(BaseConfig):
    r"""Defines the parameters for generating chat completions using the
    Gemini API.

    Args:
        temperature (float, optional): Sampling temperature to use, between
            :obj:`0` and :obj:`2`. Higher values make the output more random,
            while lower values make it more focused and deterministic.
            (default: :obj:`0.2`)
        top_p (float, optional): An alternative to sampling with temperature,
            called nucleus sampling, where the model considers the results of
            the tokens with top_p probability mass. So :obj:`0.1` means only
            the tokens comprising the top 10% probability mass are considered.
            (default: :obj:`1.0`)
        n (int, optional): How many chat completion choices to generate for
            each input message. (default: :obj:`1`)
        response_format (object, optional): An object specifying the format
            that the model must output. Compatible with GPT-4 Turbo and all
            GPT-3.5 Turbo models newer than gpt-3.5-turbo-1106. Setting to
            {"type": "json_object"} enables JSON mode, which guarantees the
            message the model generates is valid JSON. Important: when using
            JSON mode, you must also instruct the model to produce JSON
            yourself via a system or user message. Without this, the model
            may generate an unending stream of whitespace until the generation
            reaches the token limit, resulting in a long-running and seemingly
            "stuck" request. Also note that the message content may be
            partially cut off if finish_reason="length", which indicates the
            generation exceeded max_tokens or the conversation exceeded the
            max context length.
        stream (bool, optional): If True, partial message deltas will be sent
            as data-only server-sent events as they become available.
            (default: :obj:`False`)
        stop (str or list, optional): Up to :obj:`4` sequences where the API
            will stop generating further tokens. (default: :obj:`None`)
        max_tokens (int, optional): The maximum number of tokens to generate
            in the chat completion. The total length of input tokens and
            generated tokens is limited by the model's context length.
            (default: :obj:`None`)
        tools (list[FunctionTool], optional): A list of tools the model may
            call. Currently, only functions are supported as a tool. Use this
            to provide a list of functions the model may generate JSON inputs
            for. A max of 128 functions are supported.
        tool_choice (Union[dict[str, str], str], optional): Controls which (if
            any) tool is called by the model. :obj:`"none"` means the model
            will not call any tool and instead generates a message.
            :obj:`"auto"` means the model can pick between generating a
            message or calling one or more tools.  :obj:`"required"` means the
            model must call one or more tools. Specifying a particular tool
            via {"type": "function", "function": {"name": "my_function"}}
            forces the model to call that tool. :obj:`"none"` is the default
            when no tools are present. :obj:`"auto"` is the default if tools
            are present.
    """

    temperature: float = 0.2  # openai default: 1.0
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    stop: Union[str, Sequence[str], NotGiven] = NOT_GIVEN
    max_tokens: Union[int, NotGiven] = NOT_GIVEN
    response_format: Union[Type[BaseModel], dict, NotGiven] = NOT_GIVEN
    tool_choice: Optional[Union[dict[str, str], str]] = None

    def as_dict(self) -> dict[str, Any]:
        r"""Convert the current configuration to a dictionary.

        This method converts the current configuration object to a dictionary
        representation, which can be used for serialization or other purposes.

        Returns:
            dict[str, Any]: A dictionary representation of the current
                configuration.
        """
        config_dict = self.model_dump()
        if self.tools:
            from camel.toolkits import FunctionTool

            tools_schema = []
            for tool in self.tools:
                if not isinstance(tool, FunctionTool):
                    raise ValueError(f"The tool {tool} should " "be an instance of `FunctionTool`.")
                tools_schema.append(tool.get_openai_tool_schema())
        config_dict["tools"] = NOT_GIVEN
        return config_dict


Gemini_API_PARAMS = {param for param in GeminiConfig.model_fields.keys()}
