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

import os
from typing import Any, Optional

from openai import OpenAI

from camel.embeddings.base import BaseEmbedding
from camel.utils import api_keys_required


class OpenAICompatibleEmbedding(BaseEmbedding[str]):
    r"""Provides text embedding functionalities supporting OpenAI
    compatibility.

    Args:
        model_type (str): The model type to be used for text embeddings.
        api_key (str): The API key for authenticating with the model service.
        url (str): The url to the model service.
    """

    def __init__(
        self,
        model_type: str,
        api_key: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:
        self.model_type = model_type
        self.output_dim: Optional[int] = None

        self._api_key = api_key or os.environ.get("OPENAI_COMPATIBILIY_API_KEY")
        self._url = url or os.environ.get("OPENAI_COMPATIBILIY_API_BASE_URL")
        self._client = OpenAI(
            timeout=60,
            max_retries=3,
            api_key=self._api_key,
            base_url=self._url,
        )

    @api_keys_required("OPENAI_COMPATIBILIY_API_KEY")
    def embed_list(
        self,
        objs: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        r"""Generates embeddings for the given texts.

        Args:
            objs (list[str]): The texts for which to generate the embeddings.
            **kwargs (Any): Extra kwargs passed to the embedding API.

        Returns:
            list[list[float]]: A list that represents the generated embedding
                as a list of floating-point numbers.
        """

        response = self._client.embeddings.create(
            input=objs,
            model=self.model_type,
            **kwargs,
        )
        self.output_dim = len(response.data[0].embedding)
        return [data.embedding for data in response.data]

    def get_output_dim(self) -> int:
        r"""Returns the output dimension of the embeddings.

        Returns:
            int: The dimensionality of the embedding for the current model.
        """
        if self.output_dim is None:
            raise ValueError("Output dimension is not yet determined. Call " "'embed_list' first.")
        return self.output_dim
