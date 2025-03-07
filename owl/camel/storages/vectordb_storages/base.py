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

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class VectorRecord(BaseModel):
    r"""Encapsulates information about a vector's unique identifier and its
    payload, which is primarily used as a data transfer object when saving
    to vector storage.

    Attributes:
        vector (List[float]): The numerical representation of the vector.
        id (str, optional): A unique identifier for the vector. If not
            provided, an random uuid will be assigned.
        payload (Optional[Dict[str, Any]], optional): Any additional metadata
            or information related to the vector. (default: :obj:`None`)
    """

    vector: List[float]
    id: str = Field(default_factory=lambda: str(uuid4()))
    payload: Optional[Dict[str, Any]] = None


class VectorDBQuery(BaseModel):
    r"""Represents a query to a vector database.

    Attributes:
        query_vector (List[float]): The numerical representation of the query
            vector.
        top_k (int, optional): The number of top similar vectors to retrieve
            from the database. (default: :obj:`1`)
    """

    query_vector: List[float]
    """The numerical representation of the query vector."""
    top_k: int = 1
    """The number of top similar vectors to retrieve from the database."""

    def __init__(self, query_vector: List[float], top_k: int, **kwargs: Any) -> None:
        """Pass in query_vector and tok_k as positional arg.
        Args:
            query_vector (List[float]): The numerical representation of the
                query vector.
            top_k (int, optional): The number of top similar vectors to
                retrieve from the database. (default: :obj:`1`)
        """
        super().__init__(query_vector=query_vector, top_k=top_k, **kwargs)


class VectorDBQueryResult(BaseModel):
    r"""Encapsulates the result of a query against a vector database.

    Attributes:
        record (VectorRecord): The target vector record.
        similarity (float): The similarity score between the query vector and
            the record.
    """

    record: VectorRecord
    similarity: float

    @classmethod
    def create(
        cls,
        similarity: float,
        vector: List[float],
        id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> "VectorDBQueryResult":
        r"""A class method to construct a `VectorDBQueryResult` instance."""
        return cls(
            record=VectorRecord(vector=vector, id=id, payload=payload),
            similarity=similarity,
        )


class VectorDBStatus(BaseModel):
    r"""Vector database status.

    Attributes:
        vector_dim (int): The dimention of stored vectors.
        vector_count (int): The number of stored vectors.

    """

    vector_dim: int
    vector_count: int


class BaseVectorStorage(ABC):
    r"""An abstract base class for vector storage systems."""

    @abstractmethod
    def add(
        self,
        records: List[VectorRecord],
        **kwargs: Any,
    ) -> None:
        r"""Saves a list of vector records to the storage.

        Args:
            records (List[VectorRecord]): List of vector records to be saved.
            **kwargs (Any): Additional keyword arguments.

        Raises:
            RuntimeError: If there is an error during the saving process.
        """
        pass

    @abstractmethod
    def delete(
        self,
        ids: List[str],
        **kwargs: Any,
    ) -> None:
        r"""Deletes a list of vectors identified by their IDs from the storage.

        Args:
            ids (List[str]): List of unique identifiers for the vectors to be
                deleted.
            **kwargs (Any): Additional keyword arguments.

        Raises:
            RuntimeError: If there is an error during the deletion process.
        """
        pass

    @abstractmethod
    def status(self) -> VectorDBStatus:
        r"""Returns status of the vector database.

        Returns:
            VectorDBStatus: The vector database status.
        """
        pass

    @abstractmethod
    def query(
        self,
        query: VectorDBQuery,
        **kwargs: Any,
    ) -> List[VectorDBQueryResult]:
        r"""Searches for similar vectors in the storage based on the provided
        query.

        Args:
            query (VectorDBQuery): The query object containing the search
                vector and the number of top similar vectors to retrieve.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            List[VectorDBQueryResult]: A list of vectors retrieved from the
                storage based on similarity to the query vector.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        r"""Remove all vectors from the storage."""
        pass

    @abstractmethod
    def load(self) -> None:
        r"""Load the collection hosted on cloud service."""
        pass

    @property
    @abstractmethod
    def client(self) -> Any:
        r"""Provides access to the underlying vector database client."""
        pass

    def get_payloads_by_vector(
        self,
        vector: List[float],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        r"""Returns payloads of top k vector records that closest to the given
        vector.

        This function is a wrapper of `BaseVectorStorage.query`.

        Args:
            vector (List[float]): The search vector.
            top_k (int): The number of top similer vectors.

        Returns:
            List[List[Dict[str, Any]]]: A list of vector payloads retrieved
                from the storage based on similarity to the query vector.
        """
        results = self.query(VectorDBQuery(query_vector=vector, top_k=top_k))
        return [result.record.payload for result in results if result.record.payload is not None]
