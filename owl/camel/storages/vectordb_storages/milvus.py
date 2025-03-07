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
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from camel.storages.vectordb_storages import (
    BaseVectorStorage,
    VectorDBQuery,
    VectorDBQueryResult,
    VectorDBStatus,
    VectorRecord,
)
from camel.utils import dependencies_required

logger = logging.getLogger(__name__)


class MilvusStorage(BaseVectorStorage):
    r"""An implementation of the `BaseVectorStorage` for interacting with
    Milvus, a cloud-native vector search engine.

    The detailed information about Milvus is available at:
    `Milvus <https://milvus.io/docs/overview.md/>`_

    Args:
        vector_dim (int): The dimenstion of storing vectors.
        url_and_api_key (Tuple[str, str]): Tuple containing
           the URL and API key for connecting to a remote Milvus instance.
           URL maps to Milvus uri concept, typically "endpoint:port".
           API key maps to Milvus token concept, for self-hosted it's
           "username:pwd", for Zilliz Cloud (fully-managed Milvus) it's API
           Key.
        collection_name (Optional[str], optional): Name for the collection in
            the Milvus. If not provided, set it to the current time with iso
            format. (default: :obj:`None`)
        **kwargs (Any): Additional keyword arguments for initializing
            `MilvusClient`.

    Raises:
        ImportError: If `pymilvus` package is not installed.
    """

    @dependencies_required("pymilvus")
    def __init__(
        self,
        vector_dim: int,
        url_and_api_key: Tuple[str, str],
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        from pymilvus import MilvusClient

        self._client: MilvusClient
        self._create_client(url_and_api_key, **kwargs)
        self.vector_dim = vector_dim
        self.collection_name = collection_name or self._generate_collection_name()
        self._check_and_create_collection()

    def _create_client(
        self,
        url_and_api_key: Tuple[str, str],
        **kwargs: Any,
    ) -> None:
        r"""Initializes the Milvus client with the provided connection details.

        Args:
            url_and_api_key (Tuple[str, str]): The URL and API key for the
                Milvus server.
            **kwargs: Additional keyword arguments passed to the Milvus client.
        """
        from pymilvus import MilvusClient

        self._client = MilvusClient(
            uri=url_and_api_key[0],
            token=url_and_api_key[1],
            **kwargs,
        )

    def _check_and_create_collection(self) -> None:
        r"""Checks if the specified collection exists in Milvus and creates it
        if it doesn't, ensuring it matches the specified vector dimensionality.
        """
        if self._collection_exists(self.collection_name):
            in_dim = self._get_collection_info(self.collection_name)["vector_dim"]
            if in_dim != self.vector_dim:
                # The name of collection has to be confirmed by the user
                raise ValueError(
                    "Vector dimension of the existing collection "
                    f'"{self.collection_name}" ({in_dim}) is different from '
                    f"the given embedding dim ({self.vector_dim})."
                )
        else:
            self._create_collection(
                collection_name=self.collection_name,
            )

    def _create_collection(
        self,
        collection_name: str,
        **kwargs: Any,
    ) -> None:
        r"""Creates a new collection in the database.

        Args:
            collection_name (str): Name of the collection to be created.
            **kwargs (Any): Additional keyword arguments pass to create
                collection.
        """

        from pymilvus import DataType

        # Set the schema
        schema = self._client.create_schema(
            auto_id=False,
            enable_dynamic_field=True,
            description="collection schema",
        )

        schema.add_field(
            field_name="id",
            datatype=DataType.VARCHAR,
            descrition="A unique identifier for the vector",
            is_primary=True,
            max_length=65535,
        )
        # max_length reference: https://milvus.io/docs/limitations.md
        schema.add_field(
            field_name="vector",
            datatype=DataType.FLOAT_VECTOR,
            description="The numerical representation of the vector",
            dim=self.vector_dim,
        )
        schema.add_field(
            field_name="payload",
            datatype=DataType.JSON,
            description=("Any additional metadata or information related" "to the vector"),
        )

        # Create the collection
        self._client.create_collection(
            collection_name=collection_name,
            schema=schema,
            **kwargs,
        )

        # Set the index of the parameters
        index_params = self._client.prepare_index_params()

        index_params.add_index(
            field_name="vector",
            metric_type="COSINE",
            index_type="AUTOINDEX",
            index_name="vector_index",
        )

        self._client.create_index(collection_name=collection_name, index_params=index_params)

    def _delete_collection(
        self,
        collection_name: str,
    ) -> None:
        r"""Deletes an existing collection from the database.

        Args:
            collection (str): Name of the collection to be deleted.
        """
        self._client.drop_collection(collection_name=collection_name)

    def _collection_exists(self, collection_name: str) -> bool:
        r"""Checks whether a collection with the specified name exists in the
        database.

        Args:
            collection_name (str): The name of the collection to check.

        Returns:
            bool: True if the collection exists, False otherwise.
        """
        return self._client.has_collection(collection_name)

    def _generate_collection_name(self) -> str:
        r"""Generates a unique name for a new collection based on the current
        timestamp. Milvus collection names can only contain alphanumeric
        characters and underscores.

        Returns:
            str: A unique, valid collection name.
        """
        timestamp = datetime.now().isoformat()
        transformed_name = re.sub(r"[^a-zA-Z0-9_]", "_", timestamp)
        valid_name = "Time" + transformed_name
        return valid_name

    def _get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        r"""Retrieves details of an existing collection.

        Args:
            collection_name (str): Name of the collection to be checked.

        Returns:
            Dict[str, Any]: A dictionary containing details about the
                collection.
        """
        vector_count = self._client.get_collection_stats(collection_name)["row_count"]
        collection_info = self._client.describe_collection(collection_name)
        collection_id = collection_info["collection_id"]

        dim_value = next(
            (
                field["params"]["dim"]
                for field in collection_info["fields"]
                if field["description"] == "The numerical representation of the vector"
            ),
            None,
        )

        return {
            "id": collection_id,  # the id of the collection
            "vector_count": vector_count,  # the number of the vector
            "vector_dim": dim_value,  # the dimension of the vector
        }

    def _validate_and_convert_vectors(self, records: List[VectorRecord]) -> List[dict]:
        r"""Validates and converts VectorRecord instances to the format
        expected by Milvus.

        Args:
            records (List[VectorRecord]): List of vector records to validate
            and convert.

        Returns:
            List[dict]: A list of dictionaries formatted for Milvus insertion.
        """

        validated_data = []

        for record in records:
            record_dict = {
                "id": record.id,
                "payload": record.payload if record.payload is not None else "",
                "vector": record.vector,
            }
            validated_data.append(record_dict)

        return validated_data

    def add(
        self,
        records: List[VectorRecord],
        **kwargs,
    ) -> None:
        r"""Adds a list of vectors to the specified collection.

        Args:
            records (List[VectorRecord]): List of vectors to be added.
            **kwargs (Any): Additional keyword arguments pass to insert.

        Raises:
            RuntimeError: If there was an error in the addition process.
        """
        validated_records = self._validate_and_convert_vectors(records)

        op_info = self._client.insert(
            collection_name=self.collection_name,
            data=validated_records,
            **kwargs,
        )
        logger.debug(f"Successfully added vectors in Milvus: {op_info}")

    def delete(
        self,
        ids: List[str],
        **kwargs: Any,
    ) -> None:
        r"""Deletes a list of vectors identified by their IDs from the
        storage. If unsure of ids you can first query the collection to grab
        the corresponding data.

        Args:
            ids (List[str]): List of unique identifiers for the vectors to be
                deleted.
            **kwargs (Any): Additional keyword arguments passed to delete.

        Raises:
            RuntimeError: If there is an error during the deletion process.
        """

        op_info = self._client.delete(collection_name=self.collection_name, pks=ids, **kwargs)
        logger.debug(f"Successfully deleted vectors in Milvus: {op_info}")

    def status(self) -> VectorDBStatus:
        r"""Retrieves the current status of the Milvus collection. This method
        provides information about the collection, including its vector
        dimensionality and the total number of vectors stored.

        Returns:
            VectorDBStatus: An object containing information about the
                collection's status.
        """
        status = self._get_collection_info(self.collection_name)
        return VectorDBStatus(
            vector_dim=status["vector_dim"],
            vector_count=status["vector_count"],
        )

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
            **kwargs (Any): Additional keyword arguments passed to search.

        Returns:
            List[VectorDBQueryResult]: A list of vectors retrieved from the
                storage based on similarity to the query vector.
        """
        search_result = self._client.search(
            collection_name=self.collection_name,
            data=[query.query_vector],
            limit=query.top_k,
            output_fields=["vector", "payload"],
            **kwargs,
        )
        query_results = []
        for point in search_result:
            query_results.append(
                VectorDBQueryResult.create(
                    similarity=(point[0]["distance"]),
                    id=str(point[0]["id"]),
                    payload=(point[0]["entity"].get("payload")),
                    vector=point[0]["entity"].get("vector"),
                )
            )

        return query_results

    def clear(self) -> None:
        r"""Removes all vectors from the Milvus collection. This method
        deletes the existing collection and then recreates it with the same
        schema to effectively remove all stored vectors.
        """
        self._delete_collection(self.collection_name)
        self._create_collection(collection_name=self.collection_name)

    def load(self) -> None:
        r"""Load the collection hosted on cloud service."""
        self._client.load_collection(self.collection_name)

    @property
    def client(self) -> Any:
        r"""Provides direct access to the Milvus client. This property allows
        for direct interactions with the Milvus client for operations that are
        not covered by the `MilvusStorage` class.

        Returns:
            Any: The Milvus client instance.
        """
        return self._client
