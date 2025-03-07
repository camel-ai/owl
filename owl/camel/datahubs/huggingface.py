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
import json
import os
import tempfile
from typing import Any, List, Optional

from camel.datahubs.base import BaseDatasetManager
from camel.datahubs.models import Record
from camel.logger import get_logger
from camel.types import HuggingFaceRepoType
from camel.utils import api_keys_required, dependencies_required

logger = get_logger(__name__)


class HuggingFaceDatasetManager(BaseDatasetManager):
    r"""A dataset manager for Hugging Face datasets. This class provides
    methods to create, add, update, delete, and list records in a dataset on
    the Hugging Face Hub.

    Args:
        token (str): The Hugging Face API token. If not provided, the token
            will be read from the environment variable `HUGGING_FACE_TOKEN`.
    """

    @api_keys_required("HUGGING_FACE_TOKEN")
    @dependencies_required("huggingface_hub")
    def __init__(self, token: Optional[str] = None):
        from huggingface_hub import HfApi

        self._api_key = token or os.getenv("HUGGING_FACE_TOKEN")
        self.api = HfApi(token=self._api_key)

    def create_dataset_card(
        self,
        dataset_name: str,
        description: str,
        license: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        authors: Optional[List[str]] = None,
        size_category: Optional[List[str]] = None,
        language: Optional[List[str]] = None,
        task_categories: Optional[List[str]] = None,
        content: Optional[str] = None,
    ) -> None:
        r"""Creates and uploads a dataset card to the Hugging Face Hub in YAML
            format.

        Args:
            dataset_name (str): The name of the dataset.
            description (str): A description of the dataset.
            license (str): The license of the dataset. (default: :obj:`None`)
            version (str): The version of the dataset. (default: :obj:`None`)
            tags (list): A list of tags for the dataset.(default: :obj:`None`)
            authors (list): A list of authors of the dataset. (default:
                :obj:`None`)
            size_category (list): A size category for the dataset. (default:
                :obj:`None`)
            language (list): A list of languages the dataset is in. (default:
                :obj:`None`)
            task_categories (list): A list of task categories. (default:
                :obj:`None`)
            content (str): Custom markdown content that the user wants to add
                to the dataset card. (default: :obj:`None`)
        """
        import yaml

        metadata = {
            "license": license,
            "authors": authors,
            "task_categories": task_categories,
            "language": language,
            "tags": tags,
            "pretty_name": dataset_name,
            "size_categories": size_category,
            "version": version,
            "description": description,
        }

        # Remove keys with None values
        metadata = {k: v for k, v in metadata.items() if v}

        card_content = "---\n" + yaml.dump(metadata, default_flow_style=False, allow_unicode=True) + "\n---"

        if content:
            card_content += f"\n\n# Additional Information\n{content}\n"

        self._upload_file(
            file_content=card_content,
            dataset_name=dataset_name,
            filepath="README.md",
            file_type="md",
        )

    def create_dataset(self, name: str, private: bool = False, **kwargs: Any) -> str:
        r"""Creates a new dataset on the Hugging Face Hub.

        Args:
            name (str): The name of the dataset.
            private (bool): Whether the dataset should be private. defaults to
                False.
            kwargs (Any): Additional keyword arguments.

        Returns:
            str: The URL of the created dataset.
        """
        from huggingface_hub.errors import RepositoryNotFoundError

        try:
            self.api.repo_info(
                repo_id=name,
                repo_type=HuggingFaceRepoType.DATASET.value,
                **kwargs,
            )
        except RepositoryNotFoundError:
            self.api.create_repo(
                repo_id=name,
                repo_type=HuggingFaceRepoType.DATASET.value,
                private=private,
            )

        return f"https://huggingface.co/datasets/{name}"

    def list_datasets(self, username: str, limit: int = 100, **kwargs: Any) -> List[str]:
        r"""Lists all datasets for the current user.

        Args:
            username (str): The username of the user whose datasets to list.
            limit (int): The maximum number of datasets to list.
                (default: :obj:`100`)
            kwargs (Any): Additional keyword arguments.

        Returns:
            List[str]: A list of dataset ids.
        """
        try:
            return [dataset.id for dataset in self.api.list_datasets(author=username, limit=limit, **kwargs)]
        except Exception as e:
            logger.error(f"Error listing datasets: {e}")
            return []

    def delete_dataset(self, dataset_name: str, **kwargs: Any) -> None:
        r"""Deletes a dataset from the Hugging Face Hub.

        Args:
            dataset_name (str): The name of the dataset to delete.
            kwargs (Any): Additional keyword arguments.
        """
        try:
            self.api.delete_repo(
                repo_id=dataset_name,
                repo_type=HuggingFaceRepoType.DATASET.value,
                **kwargs,
            )
            logger.info(f"Dataset '{dataset_name}' deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting dataset '{dataset_name}': {e}")
            raise

    def add_records(
        self,
        dataset_name: str,
        records: List[Record],
        filepath: str = "records/records.json",
        **kwargs: Any,
    ) -> None:
        r"""Adds records to a dataset on the Hugging Face Hub.

        Args:
            dataset_name (str): The name of the dataset.
            records (List[Record]): A list of records to add to the dataset.
            filepath (str): The path to the file containing the records.
            kwargs (Any): Additional keyword arguments.

        Raises:
            ValueError: If the dataset already has a records file.
        """
        existing_records = self._download_records(dataset_name=dataset_name, filepath=filepath, **kwargs)

        if existing_records:
            raise ValueError(f"Dataset '{filepath}' already exists. " f"Use `update_records` to modify.")

        self._upload_records(
            records=records,
            dataset_name=dataset_name,
            filepath=filepath,
            **kwargs,
        )

    def update_records(
        self,
        dataset_name: str,
        records: List[Record],
        filepath: str = "records/records.json",
        **kwargs: Any,
    ) -> None:
        r"""Updates records in a dataset on the Hugging Face Hub.

        Args:
            dataset_name (str): The name of the dataset.
            records (List[Record]): A list of records to update in the dataset.
            filepath (str): The path to the file containing the records.
            kwargs (Any): Additional keyword arguments.

        Raises:
            ValueError: If the dataset does not have an existing file to update
                records in.
        """
        existing_records = self._download_records(dataset_name=dataset_name, filepath=filepath, **kwargs)

        if not existing_records:
            logger.warning(f"Dataset '{dataset_name}' does not have existing " "records. Adding new records.")
            self._upload_records(
                records=records,
                dataset_name=dataset_name,
                filepath=filepath,
                **kwargs,
            )
            return

        old_dict = {record.id: record for record in existing_records}
        new_dict = {record.id: record for record in records}
        merged_dict = old_dict.copy()
        merged_dict.update(new_dict)

        self._upload_records(
            records=list(merged_dict.values()),
            dataset_name=dataset_name,
            filepath=filepath,
            **kwargs,
        )

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
            kwargs (Any): Additional keyword arguments.

        Raises:
            ValueError: If the dataset does not have an existing file to delete
                records from.
        """
        existing_records = self._download_records(dataset_name=dataset_name, filepath=filepath, **kwargs)

        if not existing_records:
            raise ValueError(
                f"Dataset '{dataset_name}' does not have an existing file to " f"delete records from."
            )

        filtered_records = [record for record in existing_records if record.id != record_id]

        self._upload_records(
            records=filtered_records,
            dataset_name=dataset_name,
            filepath=filepath,
            **kwargs,
        )

    def list_records(
        self,
        dataset_name: str,
        filepath: str = "records/records.json",
        **kwargs: Any,
    ) -> List[Record]:
        r"""Lists all records in a dataset.

        Args:
            dataset_name (str): The name of the dataset.
            filepath (str): The path to the file containing the records.
            kwargs (Any): Additional keyword arguments.

        Returns:
            List[Record]: A list of records in the dataset.
        """
        return self._download_records(dataset_name=dataset_name, filepath=filepath, **kwargs)

    def _download_records(self, dataset_name: str, filepath: str, **kwargs: Any) -> List[Record]:
        from huggingface_hub import hf_hub_download
        from huggingface_hub.errors import EntryNotFoundError

        try:
            downloaded_file_path = hf_hub_download(
                repo_id=dataset_name,
                filename=filepath,
                repo_type=HuggingFaceRepoType.DATASET.value,
                token=self._api_key,
                **kwargs,
            )

            with open(downloaded_file_path, "r") as f:
                records_data = json.load(f)

            return [Record(**record) for record in records_data]
        except EntryNotFoundError:
            logger.info(f"No records found for dataset '{dataset_name}'.")
            return []
        except Exception as e:
            logger.error(f"Error downloading or processing records: {e}")
            raise e

    def _upload_records(
        self,
        records: List[Record],
        dataset_name: str,
        filepath: str,
        **kwargs: Any,
    ):
        with tempfile.NamedTemporaryFile(delete=False, mode="w", newline="", encoding="utf-8") as f:
            json.dump([record.model_dump() for record in records], f)
            temp_file_path = f.name

        try:
            self.api.upload_file(
                path_or_fileobj=temp_file_path,
                path_in_repo=filepath,
                repo_id=dataset_name,
                repo_type=HuggingFaceRepoType.DATASET.value,
                **kwargs,
            )
        except Exception as e:
            logger.error(f"Error uploading records file: {e}")
            raise
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _upload_file(
        self,
        file_content: str,
        dataset_name: str,
        filepath: str,
        file_type: str = "json",
        **kwargs: Any,
    ):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=f".{file_type}") as f:
            if file_type == "json":
                if isinstance(file_content, str):
                    try:
                        json_content = json.loads(file_content)
                    except json.JSONDecodeError:
                        raise ValueError("Invalid JSON string provided for file_content.")
                else:
                    try:
                        json.dumps(file_content)
                        json_content = file_content
                    except (TypeError, ValueError):
                        raise ValueError("file_content is not JSON serializable.")

                json.dump(json_content, f)
            elif file_type == "md" or file_type == "txt":
                f.write(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            temp_file_path = f.name

        try:
            self.api.upload_file(
                path_or_fileobj=temp_file_path,
                path_in_repo=filepath,
                repo_id=dataset_name,
                repo_type=HuggingFaceRepoType.DATASET.value,
                **kwargs,
            )
            logger.info(f"File uploaded successfully: {filepath}")
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
