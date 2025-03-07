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

import base64
from abc import ABC, abstractmethod
from io import BytesIO
from math import ceil
from typing import TYPE_CHECKING, List, Optional

from PIL import Image

from camel.logger import get_logger
from camel.types import (
    ModelType,
    OpenAIImageType,
    OpenAIVisionDetailType,
    UnifiedModelType,
)
from camel.utils import dependencies_required

if TYPE_CHECKING:
    from mistral_common.protocol.instruct.request import (  # type:ignore[import-not-found]
        ChatCompletionRequest,
    )

    from camel.messages import OpenAIMessage

LOW_DETAIL_TOKENS = 85
FIT_SQUARE_PIXELS = 2048
SHORTEST_SIDE_PIXELS = 768
SQUARE_PIXELS = 512
SQUARE_TOKENS = 170
EXTRA_TOKENS = 85

logger = get_logger(__name__)


def get_model_encoding(value_for_tiktoken: str):
    r"""Get model encoding from tiktoken.

    Args:
        value_for_tiktoken: Model value for tiktoken.

    Returns:
        tiktoken.Encoding: Model encoding.
    """
    import tiktoken

    try:
        encoding = tiktoken.encoding_for_model(value_for_tiktoken)
    except KeyError:
        if value_for_tiktoken in [
            ModelType.O1.value,
            ModelType.O1_MINI.value,
            ModelType.O1_PREVIEW.value,
        ]:
            encoding = tiktoken.get_encoding("o200k_base")
        else:
            logger.info("Model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
    return encoding


class BaseTokenCounter(ABC):
    r"""Base class for token counters of different kinds of models."""

    @abstractmethod
    def count_tokens_from_messages(self, messages: List[OpenAIMessage]) -> int:
        r"""Count number of tokens in the provided message list.

        Args:
            messages (List[OpenAIMessage]): Message list with the chat history
                in OpenAI API format.

        Returns:
            int: Number of tokens in the messages.
        """
        pass


class OpenAITokenCounter(BaseTokenCounter):
    def __init__(self, model: UnifiedModelType):
        r"""Constructor for the token counter for OpenAI models.

        Args:
            model (UnifiedModelType): Model type for which tokens will be
                counted.
        """
        self.model: str = model.value_for_tiktoken

        self.tokens_per_message: int
        self.tokens_per_name: int

        if self.model == "gpt-3.5-turbo-0301":
            # Every message follows <|start|>{role/name}\n{content}<|end|>\n
            self.tokens_per_message = 4
            # If there's a name, the role is omitted
            self.tokens_per_name = -1
        elif ("gpt-3.5-turbo" in self.model) or ("gpt-4" in self.model):
            self.tokens_per_message = 3
            self.tokens_per_name = 1
        elif ("o1" in self.model) or ("o3" in self.model):
            self.tokens_per_message = 2
            self.tokens_per_name = 1
        else:
            # flake8: noqa :E501
            raise NotImplementedError(
                "Token counting for OpenAI Models is not presently "
                f"implemented for model {model}. "
                "See https://github.com/openai/openai-python/blob/main/chatml.md "
                "for information on how messages are converted to tokens. "
                "See https://platform.openai.com/docs/models/gpt-4"
                "or https://platform.openai.com/docs/models/gpt-3-5"
                "for information about openai chat models."
            )

        self.encoding = get_model_encoding(self.model)

    def count_tokens_from_messages(self, messages: List[OpenAIMessage]) -> int:
        r"""Count number of tokens in the provided message list with the
        help of package tiktoken.

        Args:
            messages (List[OpenAIMessage]): Message list with the chat history
                in OpenAI API format.

        Returns:
            int: Number of tokens in the messages.
        """
        num_tokens = 0
        for message in messages:
            num_tokens += self.tokens_per_message
            for key, value in message.items():
                if not isinstance(value, list):
                    num_tokens += len(self.encoding.encode(str(value), disallowed_special=()))
                else:
                    for item in value:
                        if item["type"] == "text":
                            num_tokens += len(
                                self.encoding.encode(
                                    str(
                                        item["text"],
                                    ),
                                    disallowed_special=(),
                                )
                            )
                        elif item["type"] == "image_url":
                            image_str: str = item["image_url"]["url"]
                            detail = item["image_url"]["detail"]

                            image_prefix_format = "data:image/{};base64,"
                            image_prefix: Optional[str] = None
                            for image_type in list(OpenAIImageType):
                                # Find the correct image format
                                image_prefix = image_prefix_format.format(image_type.value)
                                if image_prefix in image_str:
                                    break
                            assert isinstance(image_prefix, str)
                            encoded_image = image_str.split(image_prefix)[1]
                            image_bytes = BytesIO(base64.b64decode(encoded_image))
                            image = Image.open(image_bytes)
                            num_tokens += self._count_tokens_from_image(image, OpenAIVisionDetailType(detail))
                if key == "name":
                    num_tokens += self.tokens_per_name

        # every reply is primed with <|start|>assistant<|message|>
        num_tokens += 3
        return num_tokens

    def _count_tokens_from_image(self, image: Image.Image, detail: OpenAIVisionDetailType) -> int:
        r"""Count image tokens for OpenAI vision model. An :obj:`"auto"`
        resolution model will be treated as :obj:`"high"`. All images with
        :obj:`"low"` detail cost 85 tokens each. Images with :obj:`"high"` detail
        are first scaled to fit within a 2048 x 2048 square, maintaining their
        aspect ratio. Then, they are scaled such that the shortest side of the
        image is 768px long. Finally, we count how many 512px squares the image
        consists of. Each of those squares costs 170 tokens. Another 85 tokens are
        always added to the final total. For more details please refer to `OpenAI
        vision docs <https://platform.openai.com/docs/guides/vision>`_

        Args:
            image (PIL.Image.Image): Image to count number of tokens.
            detail (OpenAIVisionDetailType): Image detail type to count
                number of tokens.

        Returns:
            int: Number of tokens for the image given a detail type.
        """
        if detail == OpenAIVisionDetailType.LOW:
            return LOW_DETAIL_TOKENS

        width, height = image.size
        if width > FIT_SQUARE_PIXELS or height > FIT_SQUARE_PIXELS:
            scaling_factor = max(width, height) / FIT_SQUARE_PIXELS
            width = int(width / scaling_factor)
            height = int(height / scaling_factor)

        scaling_factor = min(width, height) / SHORTEST_SIDE_PIXELS
        scaled_width = int(width / scaling_factor)
        scaled_height = int(height / scaling_factor)

        h = ceil(scaled_height / SQUARE_PIXELS)
        w = ceil(scaled_width / SQUARE_PIXELS)
        total = EXTRA_TOKENS + SQUARE_TOKENS * h * w
        return total


class AnthropicTokenCounter(BaseTokenCounter):
    @dependencies_required("anthropic")
    def __init__(self, model: str):
        r"""Constructor for the token counter for Anthropic models.

        Args:
            model (str): The name of the Anthropic model being used.
        """
        from anthropic import Anthropic

        self.client = Anthropic()
        self.model = model

    @dependencies_required("anthropic")
    def count_tokens_from_messages(self, messages: List[OpenAIMessage]) -> int:
        r"""Count number of tokens in the provided message list using
        loaded tokenizer specific for this type of model.

        Args:
            messages (List[OpenAIMessage]): Message list with the chat history
                in OpenAI API format.

        Returns:
            int: Number of tokens in the messages.
        """
        from anthropic.types import MessageParam

        return self.client.messages.count_tokens(
            messages=[
                MessageParam(
                    content=str(msg["content"]),
                    role="user" if msg["role"] == "user" else "assistant",
                )
                for msg in messages
            ],
            model=self.model,
        ).input_tokens


class GeminiTokenCounter(BaseTokenCounter):
    def __init__(self, model_type: UnifiedModelType):
        r"""Constructor for the token counter for Gemini models.

        Args:
            model_type (UnifiedModelType): Model type for which tokens will be
                counted.
        """
        import google.generativeai as genai

        self._client = genai.GenerativeModel(model_type)

    def count_tokens_from_messages(self, messages: List[OpenAIMessage]) -> int:
        r"""Count number of tokens in the provided message list using
        loaded tokenizer specific for this type of model.

        Args:
            messages (List[OpenAIMessage]): Message list with the chat history
                in OpenAI API format.

        Returns:
            int: Number of tokens in the messages.
        """
        converted_messages = []
        for message in messages:
            role = message.get("role")
            if role == "assistant":
                role_to_gemini = "model"
            else:
                role_to_gemini = "user"
            converted_message = {
                "role": role_to_gemini,
                "parts": message.get("content"),
            }
            converted_messages.append(converted_message)
        return self._client.count_tokens(converted_messages).total_tokens


class LiteLLMTokenCounter(BaseTokenCounter):
    def __init__(self, model_type: UnifiedModelType):
        r"""Constructor for the token counter for LiteLLM models.

        Args:
            model_type (UnifiedModelType): Model type for which tokens will be
                counted.
        """
        self.model_type = model_type
        self._token_counter = None
        self._completion_cost = None

    @property
    def token_counter(self):
        if self._token_counter is None:
            from litellm import token_counter

            self._token_counter = token_counter
        return self._token_counter

    @property
    def completion_cost(self):
        if self._completion_cost is None:
            from litellm import completion_cost

            self._completion_cost = completion_cost
        return self._completion_cost

    def count_tokens_from_messages(self, messages: List[OpenAIMessage]) -> int:
        r"""Count number of tokens in the provided message list using
        the tokenizer specific to this type of model.

        Args:
            messages (List[OpenAIMessage]): Message list with the chat history
                in LiteLLM API format.

        Returns:
            int: Number of tokens in the messages.
        """
        return self.token_counter(model=self.model_type, messages=messages)

    def calculate_cost_from_response(self, response: dict) -> float:
        r"""Calculate the cost of the given completion response.

        Args:
            response (dict): The completion response from LiteLLM.

        Returns:
            float: The cost of the completion call in USD.
        """
        return self.completion_cost(completion_response=response)


class MistralTokenCounter(BaseTokenCounter):
    def __init__(self, model_type: ModelType):
        r"""Constructor for the token counter for Mistral models.

        Args:
            model_type (ModelType): Model type for which tokens will be
                counted.
        """
        from mistral_common.tokens.tokenizers.mistral import (  # type:ignore[import-not-found]
            MistralTokenizer,
        )

        self.model_type = model_type

        # Determine the model type and set the tokenizer accordingly
        model_name = (
            "codestral-22b"
            if self.model_type
            in {
                ModelType.MISTRAL_CODESTRAL,
                ModelType.MISTRAL_CODESTRAL_MAMBA,
            }
            else self.model_type
        )

        self.tokenizer = MistralTokenizer.from_model(model_name)

    def count_tokens_from_messages(self, messages: List[OpenAIMessage]) -> int:
        r"""Count number of tokens in the provided message list using
        loaded tokenizer specific for this type of model.

        Args:
            messages (List[OpenAIMessage]): Message list with the chat history
                in OpenAI API format.

        Returns:
            int: Total number of tokens in the messages.
        """
        total_tokens = 0
        for msg in messages:
            tokens = self.tokenizer.encode_chat_completion(
                self._convert_response_from_openai_to_mistral(msg)
            ).tokens
            total_tokens += len(tokens)
        return total_tokens

    def _convert_response_from_openai_to_mistral(self, openai_msg: OpenAIMessage) -> ChatCompletionRequest:
        r"""Convert an OpenAI message to a Mistral ChatCompletionRequest.

        Args:
            openai_msg (OpenAIMessage): An individual message with OpenAI
                format.

        Returns:
            ChatCompletionRequest: The converted message in Mistral's request
                format.
        """

        from mistral_common.protocol.instruct.request import (
            ChatCompletionRequest,  # type:ignore[import-not-found]
        )

        mistral_request = ChatCompletionRequest(  # type: ignore[type-var]
            model=self.model_type,
            messages=[openai_msg],
        )

        return mistral_request
