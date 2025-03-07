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
import os
import warnings
from io import IOBase
from typing import IO, TYPE_CHECKING, Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from camel.embeddings import BaseEmbedding, OpenAIEmbedding
from camel.loaders import UnstructuredIO
from camel.retrievers.base import BaseRetriever
from camel.storages import (
    BaseVectorStorage,
    QdrantStorage,
    VectorDBQuery,
    VectorRecord,
)
from camel.utils import Constants

if TYPE_CHECKING:
    from unstructured.documents.elements import Element


class VectorRetriever(BaseRetriever):
    r"""An implementation of the `BaseRetriever` by using vector storage and
    embedding model.

    This class facilitates the retriever of relevant information using a
    query-based approach, backed by vector embeddings.

    Attributes:
        embedding_model (BaseEmbedding): Embedding model used to generate
            vector embeddings.
        storage (BaseVectorStorage): Vector storage to query.
        unstructured_modules (UnstructuredIO): A module for parsing files and
            URLs and chunking content based on specified parameters.
    """

    def __init__(
        self,
        embedding_model: Optional[BaseEmbedding] = None,
        storage: Optional[BaseVectorStorage] = None,
    ) -> None:
        r"""Initializes the retriever class with an optional embedding model.

        Args:
            embedding_model (Optional[BaseEmbedding]): The embedding model
                instance. Defaults to `OpenAIEmbedding` if not provided.
            storage (BaseVectorStorage): Vector storage to query.
        """
        self.embedding_model = embedding_model or OpenAIEmbedding()
        self.storage = (
            storage if storage is not None else QdrantStorage(vector_dim=self.embedding_model.get_output_dim())
        )
        self.uio: UnstructuredIO = UnstructuredIO()

    def process(
        self,
        content: Union[str, "Element", IO[bytes]],
        chunk_type: str = "chunk_by_title",
        max_characters: int = 500,
        embed_batch: int = 50,
        should_chunk: bool = True,
        extra_info: Optional[dict] = None,
        metadata_filename: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        r"""Processes content from local file path, remote URL, string
        content, Element object, or a binary file object, divides it into
        chunks by using `Unstructured IO`, and stores their embeddings in the
        specified vector storage.

        Args:
            content (Union[str, Element, IO[bytes]]): Local file path, remote
                URL, string content, Element object, or a binary file object.
            chunk_type (str): Type of chunking going to apply. Defaults to
                "chunk_by_title".
            max_characters (int): Max number of characters in each chunk.
                Defaults to `500`.
            embed_batch (int): Size of batch for embeddings. Defaults to `50`.
            should_chunk (bool): If True, divide the content into chunks,
                otherwise skip chunking. Defaults to True.
            extra_info (Optional[dict]): Extra information to be added
                to the payload. Defaults to None.
            metadata_filename (Optional[str]): The metadata filename to be
                used for storing metadata. Defaults to None.
            **kwargs (Any): Additional keyword arguments for content parsing.
        """

        def sanitize_text(text: str):
            if not text:
                return " "
            return text

        from unstructured.documents.elements import Element

        if isinstance(content, Element):
            elements = [content]
        elif isinstance(content, IOBase):
            elements = self.uio.parse_bytes(file=content, metadata_filename=metadata_filename, **kwargs) or []
        elif isinstance(content, str):
            # Check if the content is URL
            parsed_url = urlparse(content)
            is_url = all([parsed_url.scheme, parsed_url.netloc])
            if is_url or os.path.exists(content):
                elements = (
                    self.uio.parse_file_or_url(
                        input_path=content,
                        metadata_filename=metadata_filename,
                        **kwargs,
                    )
                    or []
                )
            else:
                elements = [
                    self.uio.create_element_from_text(
                        text=content,
                        filename=metadata_filename,
                    )
                ]

        if not elements:
            warnings.warn(f"No elements were extracted from the content: {content}")
        else:
            # Chunk the content if required
            chunks = (
                self.uio.chunk_elements(
                    chunk_type=chunk_type,
                    elements=elements,
                    max_characters=max_characters,
                )
                if should_chunk
                else elements
            )
            # Process chunks in batches and store embeddings
            for i in range(0, len(chunks), embed_batch):
                batch_chunks = chunks[i : i + embed_batch]
                batch_vectors = self.embedding_model.embed_list(
                    objs=[sanitize_text(str(chunk)) for chunk in batch_chunks]
                )

                records = []
                # Prepare the payload for each vector record, includes the
                # content path, chunk metadata, and chunk text
                for vector, chunk in zip(batch_vectors, batch_chunks):
                    if isinstance(content, str):
                        content_path_info = {"content path": content}
                    elif isinstance(content, IOBase):
                        content_path_info = {"content path": "From file bytes"}
                    elif isinstance(content, Element):
                        content_path_info = {"content path": content.metadata.file_directory or ""}

                    chunk_metadata = {"metadata": chunk.metadata.to_dict()}
                    # Remove the 'orig_elements' key if it exists
                    chunk_metadata["metadata"].pop("orig_elements", "")
                    chunk_metadata["extra_info"] = extra_info or {}
                    chunk_text = {"text": str(chunk)}
                    combined_dict = {
                        **content_path_info,
                        **chunk_metadata,
                        **chunk_text,
                    }

                    records.append(VectorRecord(vector=vector, payload=combined_dict))

                self.storage.add(records=records)

    def query(
        self,
        query: str,
        top_k: int = Constants.DEFAULT_TOP_K_RESULTS,
        similarity_threshold: float = Constants.DEFAULT_SIMILARITY_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        r"""Executes a query in vector storage and compiles the retrieved
        results into a dictionary.

        Args:
            query (str): Query string for information retriever.
            similarity_threshold (float, optional): The similarity threshold
                for filtering results. Defaults to
                `DEFAULT_SIMILARITY_THRESHOLD`.
            top_k (int, optional): The number of top results to return during
                retriever. Must be a positive integer. Defaults to
                `DEFAULT_TOP_K_RESULTS`.

        Returns:
            List[Dict[str, Any]]: Concatenated list of the query results.

        Raises:
            ValueError: If 'top_k' is less than or equal to 0, if vector
                storage is empty, if payload of vector storage is None.
        """

        if top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        # Load the storage incase it's hosted remote
        self.storage.load()

        query_vector = self.embedding_model.embed(obj=query)
        db_query = VectorDBQuery(query_vector=query_vector, top_k=top_k)
        query_results = self.storage.query(query=db_query)

        # If no results found, raise an error
        if not query_results:
            raise ValueError("Query result is empty, please check if " "the vector storage is empty.")

        if query_results[0].record.payload is None:
            raise ValueError("Payload of vector storage is None, please check the " "collection.")

        # format the results
        formatted_results = []
        for result in query_results:
            if result.similarity >= similarity_threshold and result.record.payload is not None:
                result_dict = {
                    "similarity score": str(result.similarity),
                    "content path": result.record.payload.get("content path", ""),
                    "metadata": result.record.payload.get("metadata", {}),
                    "extra_info": result.record.payload.get("extra_info", {}),
                    "text": result.record.payload.get("text", ""),
                }
                formatted_results.append(result_dict)

        content_path = query_results[0].record.payload.get("content path", "")

        if not formatted_results:
            return [
                {
                    "text": (
                        f"No suitable information retrieved "
                        f"from {content_path} with similarity_threshold"
                        f" = {similarity_threshold}."
                    )
                }
            ]
        return formatted_results
