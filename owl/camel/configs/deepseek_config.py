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


class DeepSeekConfig(BaseConfig):
    r"""Defines the parameters for generating chat completions using the
    DeepSeek API.

    Args:
        temperature (float, optional): Sampling temperature to use, between
            :obj:`0` and :obj:`2`. Higher values make the output more random,
            while lower values make it more focused and deterministic.
            (default: :obj:`0.2`)
        top_p (float, optional): Controls the diversity and focus of the
            generated results. Higher values make the output more diverse,
            while lower values make it more focused. (default: :obj:`1.0`)
        response_format (object, optional): Specifies the format of the
            returned content. The available values are `{"type": "text"}` or
            `{"type": "json_object"}`. Setting it to `{"type": "json_object"}`
            will output a standard JSON string.
            (default: :obj:`{"type": "text"}`)
        stream (bool, optional): If set, partial message deltas will be sent.
            Tokens will be sent as data-only server-sent events (SSE) as
            they become available, with the stream terminated by a
            data: [DONE] message. (default: :obj:`False`)
        stop (Union[str, list[str]], optional): Up to 16 sequences where
            the API will stop generating further tokens. (default: :obj:`None`)
        max_tokens (int, optional): The maximum number of tokens that can
            be generated in the chat completion. The total length of input
            tokens and generated tokens is limited by the model's context
            length. (default: :obj:`None`)
        presence_penalty (float, optional): Number between -2.0 and 2.0.
            Positive values penalize new tokens based on whether they
            appear in the text so far, increasing the model's likelihood
            to talk about new topics. (default: :obj:`0.0`)
        frequency_penalty (float, optional): Number between -2.0 and 2.0.
            Positive values penalize new tokens based on their existing
            frequency in the text so far, decreasing the model's likelihood
            to repeat the same line verbatim. (default: :obj:`0`)
        tools (list[FunctionTool], optional): A list of tools the model may
            call. Currently, only functions are supported as a tool. Use
            this to provide a list of functions the model may generate JSON
            inputs for. A max of 128 functions are supported.
            (default: :obj:`None`)
        tool_choice (Union[dict[str, str], str], optional): Controls which
            (if any) tool is called by the model. "none" means the model
            will not call any tool and instead generates a message. "auto"
            means the model can pick between generating a message or calling
            one or more tools. "required" means the model must call one or
            more tools. Specifying a particular tool via
            {"type": "function", "function": {"name": "my_function"}} forces
            the model to call that tool. "none" is the default when no tools
            are present. "auto" is the default if tools are present.
            (default: :obj:`"auto"`)
        logprobs (bool, optional): Whether to return log probabilities of
            the output tokens or not. If true, returns the log probabilities
            of each output token returned in the content of message.
            (default: :obj:`False`)
        top_logprobs (int, optional): An integer between 0 and 20 specifying
            the number of most likely tokens to return at each token
            position, each with an associated log probability. logprobs
            must be set to true if this parameter is used.
            (default: :obj:`None`)
        include_usage (bool, optional): When streaming, specifies whether to
            include usage information in `stream_options`. (default:
            :obj:`True`)
    """

    temperature: float = 0.2  # deepseek default: 1.0
    top_p: float = 1.0
    stream: bool = False
    stop: Union[str, Sequence[str], NotGiven] = NOT_GIVEN
    max_tokens: Union[int, NotGiven] = NOT_GIVEN
    presence_penalty: float = 0.0
    response_format: Union[Type[BaseModel], dict, NotGiven] = NOT_GIVEN
    frequency_penalty: float = 0.0
    tool_choice: Optional[Union[dict[str, str], str]] = None
    logprobs: bool = False
    top_logprobs: Optional[int] = None

    def __init__(self, include_usage: bool = True, **kwargs):
        super().__init__(**kwargs)
        # Only set stream_options when stream is True
        # Otherwise, it will raise error when calling the API
        if self.stream:
            self.stream_options = {"include_usage": include_usage}

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


DEEPSEEK_API_PARAMS = {param for param in DeepSeekConfig.model_fields.keys()}
