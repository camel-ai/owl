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
from typing import Any, List

from camel.datahubs.models import Record


class BaseDatasetManager(ABC):
    r"""Abstract base class for dataset managers."""

    @abstractmethod
    def create_dataset(self, name: str, **kwargs: Any) -> str:
        r"""Creates a new dataset.

        Args:
            name (str): The name of the dataset.
            kwargs (Any): Additional keyword arguments.

        Returns:
            str: The URL of the created dataset.
        """
        pass

    @abstractmethod
    def list_datasets(self, username: str, limit: int = 100, **kwargs: Any) -> List[str]:
        r"""Lists all datasets for the current user.

        Args:
            username (str): The username of the user whose datasets to list.
            limit (int): The maximum number of datasets to list.
                (default::obj:`100`)
            kwargs (Any): Additional keyword arguments.

        Returns:
            List[str]: A list of dataset ids.
        """
        pass

    @abstractmethod
    def delete_dataset(self, dataset_name: str, **kwargs: Any) -> None:
        r"""Deletes a dataset.

        Args:
            dataset_name (str): The name of the dataset to delete.
            kwargs (Any): Additional keyword arguments.
        """
        pass

    @abstractmethod
    def add_records(
        self,
        dataset_name: str,
        records: List[Record],
        filepath: str = "records/records.json",
        **kwargs: Any,
    ) -> None:
        r"""Adds records to a dataset.

        Args:
            dataset_name (str): The name of the dataset.
            records (List[Record]): A list of records to add to the dataset.
            filepath (str): The path to the file containing the records.
                (default::obj:`"records/records.json"`)
            kwargs (Any): Additional keyword arguments.
        """
        pass

    @abstractmethod
    def update_records(
        self,
        dataset_name: str,
        records: List[Record],
        filepath: str = "records/records.json",
        **kwargs: Any,
    ) -> None:
        r"""Updates records in a dataset.

        Args:
            dataset_name (str): The name of the dataset.
            records (List[Record]): A list of records to update in the dataset.
            filepath (str): The path to the file containing the records.
                (default::obj:`"records/records.json"`)
            kwargs (Any): Additional keyword arguments.
        """
        pass

    @abstractmethod
    def list_records(
        self,
        dataset_name: str,
        filepath: str = "records/records.json",
        **kwargs: Any,
    ) -> List[Record]:
        r"""Lists records in a dataset.

        Args:
            dataset_name (str): The name of the dataset.
            filepath (str): The path to the file containing the records.
                (default::obj:`"records/records.json"`)
            kwargs (Any): Additional keyword arguments.
        """
        pass

    # New method for record deletion
    @abstractmethod
    def delete_record(
        self,
        dataset_name: str,
        record_id: str,
        filepath: str = "records/records.json",
        **kwargs: Any,
    ) -> None:
        r"""Deletes a record from the dataset.

        Args:
            dataset_name (str): The name of the dataset.
            record_id (str): The ID of the record to delete.
            filepath (str): The path to the file containing the records.
                (default::obj:`"records/records.json"`)
            kwargs (Any): Additional keyword arguments.
        """
        pass
