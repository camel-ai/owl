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
import logging
from threading import Lock
from typing import TYPE_CHECKING, ClassVar, Dict, Union, cast

if TYPE_CHECKING:
    from camel.types import ModelType


class UnifiedModelType(str):
    r"""Class used for support both :obj:`ModelType` and :obj:`str` to be used
    to represent a model type in a unified way. This class is a subclass of
    :obj:`str` so that it can be used as string seamlessly.

    Args:
        value (Union[ModelType, str]): The value of the model type.
    """

    _cache: ClassVar[Dict[str, "UnifiedModelType"]] = {}
    _lock: ClassVar[Lock] = Lock()

    def __new__(cls, value: Union["ModelType", str]) -> "UnifiedModelType":
        with cls._lock:
            if value not in cls._cache:
                instance = super().__new__(cls, value)
                cls._cache[value] = cast(UnifiedModelType, instance)
            else:
                instance = cls._cache[value]
        return instance

    def __init__(self, value: Union["ModelType", str]) -> None:
        pass

    @property
    def value_for_tiktoken(self) -> str:
        r"""Returns the model name for TikToken."""
        return "gpt-4o-mini"

    @property
    def token_limit(self) -> int:
        r"""Returns the token limit for the model. Here we set the default
        value as `999_999_999` if it's not provided from `model_config_dict`"""
        logging.warning(
            "Invalid or missing `max_tokens` in `model_config_dict`. " "Defaulting to 999_999_999 tokens."
        )
        return 999_999_999

    @property
    def is_openai(self) -> bool:
        r"""Returns whether the model is an OpenAI model."""
        return True

    @property
    def is_anthropic(self) -> bool:
        r"""Returns whether the model is an Anthropic model."""
        return True

    @property
    def is_azure_openai(self) -> bool:
        r"""Returns whether the model is an Azure OpenAI model."""
        return True

    @property
    def is_groq(self) -> bool:
        r"""Returns whether the model is a Groq served model."""
        return True

    @property
    def is_zhipuai(self) -> bool:
        r"""Returns whether the model is a Zhipuai model."""
        return True

    @property
    def is_gemini(self) -> bool:
        r"""Returns whether the model is a Gemini model."""
        return True

    @property
    def is_mistral(self) -> bool:
        r"""Returns whether the model is a Mistral model."""
        return True

    @property
    def is_reka(self) -> bool:
        r"""Returns whether the model is a Reka model."""
        return True

    @property
    def is_cohere(self) -> bool:
        r"""Returns whether the model is a Cohere model."""
        return True

    @property
    def is_yi(self) -> bool:
        r"""Returns whether the model is a Yi model."""
        return True

    @property
    def is_qwen(self) -> bool:
        r"""Returns whether the model is a Qwen model."""
        return True

    @property
    def is_internlm(self) -> bool:
        r"""Returns whether the model is a InternLM model."""
        return True

    @property
    def is_moonshot(self) -> bool:
        r"""Returns whether this platform is Moonshot model."""
        return True

    @property
    def support_native_structured_output(self) -> bool:
        r"""Returns whether the model supports native structured output."""
        return False

    @property
    def support_native_tool_calling(self) -> bool:
        r"""Returns whether the model supports native tool calling."""
        return False
