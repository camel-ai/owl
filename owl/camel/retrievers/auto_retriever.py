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
import re
import uuid
from typing import (
    TYPE_CHECKING,
    Collection,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from camel.embeddings import BaseEmbedding, OpenAIEmbedding
from camel.retrievers.vector_retriever import VectorRetriever
from camel.storages import (
    BaseVectorStorage,
    MilvusStorage,
    QdrantStorage,
)
from camel.types import StorageType
from camel.utils import Constants

if TYPE_CHECKING:
    from unstructured.documents.elements import Element


class AutoRetriever:
    r"""Facilitates the automatic retrieval of information using a
    query-based approach with pre-defined elements.

    Attributes:
        url_and_api_key (Optional[Tuple[str, str]]): URL and API key for
            accessing the vector storage remotely.
        vector_storage_local_path (Optional[str]): Local path for vector
            storage, if applicable.
        storage_type (Optional[StorageType]): The type of vector storage to
            use. Defaults to `StorageType.QDRANT`.
        embedding_model (Optional[BaseEmbedding]): Model used for embedding
            queries and documents. Defaults to `OpenAIEmbedding()`.
    """

    def __init__(
        self,
        url_and_api_key: Optional[Tuple[str, str]] = None,
        vector_storage_local_path: Optional[str] = None,
        storage_type: Optional[StorageType] = None,
        embedding_model: Optional[BaseEmbedding] = None,
    ):
        self.storage_type = storage_type or StorageType.QDRANT
        self.embedding_model = embedding_model or OpenAIEmbedding()
        self.vector_storage_local_path = vector_storage_local_path
        self.url_and_api_key = url_and_api_key

    def _initialize_vector_storage(
        self,
        collection_name: Optional[str] = None,
    ) -> BaseVectorStorage:
        r"""Sets up and returns a vector storage instance with specified
        parameters.

        Args:
            collection_name (Optional[str]): Name of the collection in the
                vector storage.

        Returns:
            BaseVectorStorage: Configured vector storage instance.
        """
        if self.storage_type == StorageType.MILVUS:
            if self.url_and_api_key is None:
                raise ValueError("URL and API key required for Milvus storage are not" "provided.")
            return MilvusStorage(
                vector_dim=self.embedding_model.get_output_dim(),
                collection_name=collection_name,
                url_and_api_key=self.url_and_api_key,
            )

        if self.storage_type == StorageType.QDRANT:
            return QdrantStorage(
                vector_dim=self.embedding_model.get_output_dim(),
                collection_name=collection_name,
                path=self.vector_storage_local_path,
                url_and_api_key=self.url_and_api_key,
            )

        raise ValueError(f"Unsupported vector storage type: {self.storage_type}")

    def _collection_name_generator(self, content: Union[str, "Element"]) -> str:
        r"""Generates a valid collection name from a given file path or URL.

        Args:
            content (Union[str, Element]): Local file path, remote URL,
                string content or Element object.

        Returns:
            str: A sanitized, valid collection name suitable for use.
        """
        from unstructured.documents.elements import Element

        if isinstance(content, Element):
            content = content.metadata.file_directory or str(uuid.uuid4())

        collection_name = re.sub(r"[^a-zA-Z0-9]", "", content)[:20]

        return collection_name

    def run_vector_retriever(
        self,
        query: str,
        contents: Union[str, List[str], "Element", List["Element"]],
        top_k: int = Constants.DEFAULT_TOP_K_RESULTS,
        similarity_threshold: float = Constants.DEFAULT_SIMILARITY_THRESHOLD,
        return_detailed_info: bool = False,
        max_characters: int = 500,
    ) -> dict[str, Sequence[Collection[str]]]:
        r"""Executes the automatic vector retriever process using vector
        storage.

        Args:
            query (str): Query string for information retriever.
            contents (Union[str, List[str], Element, List[Element]]): Local
                file paths, remote URLs, string contents or Element objects.
            top_k (int, optional): The number of top results to return during
                retrieve. Must be a positive integer. Defaults to
                `DEFAULT_TOP_K_RESULTS`.
            similarity_threshold (float, optional): The similarity threshold
                for filtering results. Defaults to
                `DEFAULT_SIMILARITY_THRESHOLD`.
            return_detailed_info (bool, optional): Whether to return detailed
                information including similarity score, content path and
                metadata. Defaults to `False`.
            max_characters (int): Max number of characters in each chunk.
                Defaults to `500`.

        Returns:
            dict[str, Sequence[Collection[str]]]: By default, returns
                only the text information. If `return_detailed_info` is
                `True`, return detailed information including similarity
                score, content path and metadata.

        Raises:
            ValueError: If there's an vector storage existing with content
                name in the vector path but the payload is None. If
                `contents` is empty.
            RuntimeError: If any errors occur during the retrieve process.
        """
        from unstructured.documents.elements import Element

        if not contents:
            raise ValueError("content cannot be empty.")

        # Normalize contents to a list
        if isinstance(contents, str):
            contents = [contents]
        elif isinstance(contents, Element):
            contents = [contents]
        elif not isinstance(contents, list):
            raise ValueError("contents must be a string, Element, or a list of them.")
        all_retrieved_info = []
        for content in contents:
            # Generate a valid collection name
            collection_name = self._collection_name_generator(content)
            try:
                vector_storage_instance = self._initialize_vector_storage(collection_name)

                if vector_storage_instance.status().vector_count == 0:
                    # Clear the vector storage
                    vector_storage_instance.clear()
                    # Process and store the content to the vector storage
                    vr = VectorRetriever(
                        storage=vector_storage_instance,
                        embedding_model=self.embedding_model,
                    )
                    vr.process(content=content, max_characters=max_characters)
                else:
                    vr = VectorRetriever(
                        storage=vector_storage_instance,
                        embedding_model=self.embedding_model,
                    )
                # Retrieve info by given query from the vector storage
                retrieved_info = vr.query(query, top_k, similarity_threshold)
                all_retrieved_info.extend(retrieved_info)
            except Exception as e:
                raise RuntimeError(f"Error in auto vector retriever processing: {e!s}") from e

        # Split records into those with and without a 'similarity_score'
        # Records with 'similarity_score' lower than 'similarity_threshold'
        # will not have a 'similarity_score' in the output content
        with_score = [info for info in all_retrieved_info if "similarity score" in info]
        without_score = [info for info in all_retrieved_info if "similarity score" not in info]
        # Sort only the list with scores
        with_score_sorted = sorted(with_score, key=lambda x: x["similarity score"], reverse=True)
        # Merge back the sorted scored items with the non-scored items
        all_retrieved_info_sorted = with_score_sorted + without_score
        # Select the 'top_k' results
        all_retrieved_info = all_retrieved_info_sorted[:top_k]

        text_retrieved_info = [item["text"] for item in all_retrieved_info]

        detailed_info = {
            "Original Query": query,
            "Retrieved Context": all_retrieved_info,
        }

        text_info = {
            "Original Query": query,
            "Retrieved Context": text_retrieved_info,
        }
        # breakpoint()

        if return_detailed_info:
            return detailed_info
        else:
            return text_info
