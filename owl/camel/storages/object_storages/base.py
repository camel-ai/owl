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
from pathlib import Path, PurePath
from typing import Tuple

from camel.loaders import File


class BaseObjectStorage(ABC):
    def object_exists(self, file_path: PurePath) -> bool:
        r"""Check if the object exists in the storage.

        Args:
            file_path (PurePath): The path to the object in the storage.

        Returns:
            bool: True if the object exists, False otherwise.
        """
        file_key, _ = self.canonicalize_path(file_path)
        return self._object_exists(file_key)

    @staticmethod
    @abstractmethod
    def canonicalize_path(file_path: PurePath) -> Tuple[str, str]:
        pass

    def put_file(self, file_path: PurePath, file: File) -> None:
        r"""Put a file to the object storage.

        Args:
            file_path (PurePath): The path to the object in the storage.
            file (File): The file to be put.
        """
        file_key, _ = self.canonicalize_path(file_path)
        self._put_file(file_key, file)

    def get_file(self, file_path: PurePath) -> File:
        r"""Get a file from the object storage.

        Args:
            file_path (PurePath): The path to the object in the storage.

        Returns:
            File: The file object get from the storage.
        """
        file_key, filename = self.canonicalize_path(file_path)
        return self._get_file(file_key, filename)

    def upload_file(self, local_file_path: Path, remote_file_path: PurePath) -> None:
        r"""Upload a local file to the object storage.

        Args:
            local_file_path (Path): The path to the local file to be uploaded.
            remote_file_path (PurePath): The path to the object in storage.
        """
        file_key, _ = self.canonicalize_path(remote_file_path)
        # check if the local file exists
        if not local_file_path.exists():
            raise FileNotFoundError(f"Local file {local_file_path} does not exist.")
        self._upload_file(local_file_path, file_key)

    def download_file(self, local_file_path: Path, remote_file_path: PurePath) -> None:
        r"""Download a file from the object storage to the local system.

        Args:
            local_file_path (Path): The path to the local file to be saved.
            remote_file_path (PurePath): The path to the object in storage.
        """
        file_key, _ = self.canonicalize_path(remote_file_path)
        self._download_file(local_file_path, file_key)

    @abstractmethod
    def _put_file(self, file_key: str, file: File) -> None:
        pass

    @abstractmethod
    def _get_file(self, file_key: str, filename: str) -> File:
        pass

    @abstractmethod
    def _object_exists(self, file_key: str) -> bool:
        pass

    @abstractmethod
    def _upload_file(self, local_file_path: Path, remote_file_key: str) -> None:
        pass

    @abstractmethod
    def _download_file(
        self,
        local_file_path: Path,
        remote_file_key: str,
    ) -> None:
        pass
