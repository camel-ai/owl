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

from typing import Any

from numpy import ndarray

from camel.embeddings.base import BaseEmbedding


class SentenceTransformerEncoder(BaseEmbedding[str]):
    r"""This class provides functionalities to generate text
    embeddings using `Sentence Transformers`.

    References:
        https://www.sbert.net/
    """

    def __init__(
        self,
        model_name: str = "intfloat/e5-large-v2",
        **kwargs,
    ):
        r"""Initializes the: obj: `SentenceTransformerEmbedding` class
        with the specified transformer model.

        Args:
            model_name (str, optional): The name of the model to use.
                (default: :obj:`intfloat/e5-large-v2`)
            **kwargs (optional): Additional arguments of
                :class:`SentenceTransformer`, such as :obj:`prompts` etc.
        """
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name, **kwargs)

    def embed_list(
        self,
        objs: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        r"""Generates embeddings for the given texts using the model.

        Args:
            objs (list[str]): The texts for which to generate the
                embeddings.

        Returns:
            list[list[float]]: A list that represents the generated embedding
                as a list of floating-point numbers.
        """
        if not objs:
            raise ValueError("Input text list is empty")
        embeddings = self.model.encode(objs, normalize_embeddings=True, **kwargs)
        assert isinstance(embeddings, ndarray)
        return embeddings.tolist()

    def get_output_dim(self) -> int:
        r"""Returns the output dimension of the embeddings.

        Returns:
            int: The dimensionality of the embeddings.
        """
        output_dim = self.model.get_sentence_embedding_dimension()
        assert isinstance(output_dim, int)
        return output_dim
