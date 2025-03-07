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
from pathlib import Path, PurePath
from typing import Optional, Tuple
from warnings import warn

from camel.loaders import File
from camel.storages.object_storages.base import BaseObjectStorage


class AzureBlobStorage(BaseObjectStorage):
    r"""A class to connect to Azure Blob Storage. It will connect to one
    container in the storage account.

    Args:
        storage_account_name (str): The name of the storage account.
        container_name (str): The name of the container.
        access_key (Optional[str], optional): The access key of the storage
            account. Defaults to None.

    References:
        https://azure.microsoft.com/en-us/products/storage/blobs
    """

    def __init__(
        self,
        storage_account_name: str,
        container_name: str,
        create_if_not_exists: bool = True,
        access_key: Optional[str] = None,
    ) -> None:
        access_key = access_key or os.getenv("AZURE_ACCESS_KEY")
        self._create_if_not_exists = create_if_not_exists

        if not access_key:
            warn("AZURE_ACCESS_KEY not provided.")
            # Make all the empty values None
            access_key = None

        from azure.storage.blob import ContainerClient

        self._client = ContainerClient(
            account_url="https://" f"{storage_account_name}.blob.core.windows.net",
            credential=access_key,
            container_name=container_name,
        )

        self._prepare_and_check()

    def _prepare_and_check(self) -> None:
        r"""Check privileges and existence of the container."""
        from azure.core.exceptions import ClientAuthenticationError

        try:
            exists = self._client.exists()
            if not exists and self._create_if_not_exists:
                self._client.create_container()
                warn(f"Container {self._client.container_name} not found. " f"Automatically created.")
            elif not exists:
                raise FileNotFoundError(
                    f"Failed to access container {self._client.container_name}" f": Not found."
                )
        except ClientAuthenticationError:
            raise PermissionError(f"Failed to access container {self._client.container_name}: " f"No permission.")

    @staticmethod
    def canonicalize_path(file_path: PurePath) -> Tuple[str, str]:
        r"""Canonicalize file path for Azure Blob Storage.

        Args:
            file_path (PurePath): The path to be canonicalized.

        Returns:
            Tuple[str, str]: The canonicalized file key and file name.
        """
        # for Azure, both slash and backslash will be treated as separator
        filename = file_path.name
        if "\\" in filename:
            raise ValueError("Azure Blob Storage does not support backslash in filename.")
        return file_path.as_posix(), filename

    def _put_file(self, file_key: str, file: File) -> None:
        r"""Put a file to the Azure Blob Storage container.

        Args:
            file_key (str): The path to the object in the container.
            file (File): The file to be uploaded.
        """
        self._client.upload_blob(name=file_key, data=file.raw_bytes, overwrite=True)

    def _get_file(self, file_key: str, filename: str) -> File:
        r"""Get a file from the Azure Blob Storage container.

        Args:
            file_key (str): The path to the object in the container.
            filename (str): The name of the file.

        Returns:
            File: The object from the container.
        """
        raw_bytes = self._client.download_blob(file_key).readall()
        file = File.create_file_from_raw_bytes(raw_bytes, filename)
        return file

    def _upload_file(self, local_file_path: Path, remote_file_key: str) -> None:
        r"""Upload a local file to the Azure Blob Storage container.

        Args:
            local_file_path (Path): The path to the local file to be uploaded.
            remote_file_key (str): The path to the object in the container.
        """
        with open(local_file_path, "rb") as f:
            self._client.upload_blob(name=remote_file_key, data=f, overwrite=True)

    def _download_file(self, local_file_path: Path, remote_file_key: str) -> None:
        r"""Download a file from the Azure Blob Storage container to the local
        system.

        Args:
            local_file_path (Path): The path to the local file to be saved.
            remote_file_key (str): The key of the object in the container.
        """
        with open(local_file_path, "wb") as f:
            f.write(self._client.download_blob(remote_file_key).readall())

    def _object_exists(self, file_key: str) -> bool:
        r"""
        Check if the object exists in the Azure Blob Storage container.

        Args:
            file_key: The key of the object in the container.

        Returns:
            bool: Whether the object exists in the container.
        """
        return self._client.get_blob_client(file_key).exists()
