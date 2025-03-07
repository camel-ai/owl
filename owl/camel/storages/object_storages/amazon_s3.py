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


class AmazonS3Storage(BaseObjectStorage):
    r"""A class to connect with AWS S3 object storage to put and get objects
    from one S3 bucket. The class will first try to use the credentials passed
    as arguments, if not provided, it will look for the environment variables
    `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. If none of these are
    provided, it will try to use the local credentials (will be created if
    logged in with AWS CLI).

    Args:
        bucket_name (str): The name of the S3 bucket.
        create_if_not_exists (bool, optional): Whether to create the bucket if
            it does not exist. Defaults to True.
        access_key_id (Optional[str], optional): The AWS access key ID.
            Defaults to None.
        secret_access_key (Optional[str], optional): The AWS secret access key.
            Defaults to None.
        anonymous (bool, optional): Whether to use anonymous access. Defaults
            to False.

    References:
        https://aws.amazon.com/pm/serv-s3/

        https://aws.amazon.com/cli/
    """

    def __init__(
        self,
        bucket_name: str,
        create_if_not_exists: bool = True,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        anonymous: bool = False,
    ) -> None:
        self._bucket_name = bucket_name
        self._create_if_not_exists = create_if_not_exists

        aws_key_id = access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        if not all([aws_key_id, aws_secret_key]) and not anonymous:
            warn("AWS access key not configured. Local credentials will be " "used.")
            # Make all the empty values None
            aws_key_id = None
            aws_secret_key = None

        import botocore.session
        from botocore import UNSIGNED
        from botocore.config import Config

        session = botocore.session.get_session()

        if not anonymous:
            self._client = session.create_client(
                "s3",
                aws_access_key_id=aws_key_id,
                aws_secret_access_key=aws_secret_key,
            )
        else:
            self._client = session.create_client("s3", config=Config(signature_version=UNSIGNED))

        self._prepare_and_check()

    def _prepare_and_check(self) -> None:
        r"""Check privileges and existence of the bucket."""
        from botocore.exceptions import ClientError, NoCredentialsError

        try:
            self._client.head_bucket(Bucket=self._bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "403":
                raise PermissionError(f"Failed to access bucket {self._bucket_name}: " f"No permission.")
            elif error_code == "404":
                if self._create_if_not_exists:
                    self._client.create_bucket(Bucket=self._bucket_name)
                    warn(f"Bucket {self._bucket_name} not found. Automatically " f"created.")
                else:
                    raise FileNotFoundError(f"Failed to access bucket {self._bucket_name}: Not " f"found.")
            else:
                raise e
        except NoCredentialsError as e:
            raise PermissionError("No AWS credentials found.") from e

    @staticmethod
    def canonicalize_path(file_path: PurePath) -> Tuple[str, str]:
        r"""Canonicalize file path for Amazon S3.

        Args:
            file_path (PurePath): The path to be canonicalized.

        Returns:
            Tuple[str, str]: The canonicalized file key and file name.
        """
        return file_path.as_posix(), file_path.name

    def _put_file(self, file_key: str, file: File) -> None:
        r"""Put a file to the Amazon S3 bucket.

        Args:
            file_key (str): The path to the object in the bucket.
            file (File): The file to be uploaded.
        """
        self._client.put_object(Bucket=self._bucket_name, Key=file_key, Body=file.raw_bytes)

    def _get_file(self, file_key: str, filename: str) -> File:
        r"""Get a file from the Amazon S3 bucket.

        Args:
            file_key (str): The path to the object in the bucket.
            filename (str): The name of the file.

        Returns:
            File: The object from the S3 bucket.
        """
        response = self._client.get_object(Bucket=self._bucket_name, Key=file_key)
        raw_bytes = response["Body"].read()
        return File.create_file_from_raw_bytes(raw_bytes, filename)

    def _upload_file(self, local_file_path: Path, remote_file_key: str) -> None:
        r"""Upload a local file to the Amazon S3 bucket.

        Args:
            local_file_path (Path): The path to the local file to be uploaded.
            remote_file_key (str): The path to the object in the bucket.
        """
        with open(local_file_path, "rb") as f:
            self._client.put_object(Bucket=self._bucket_name, Key=remote_file_key, Body=f)

    def _download_file(
        self,
        local_file_path: Path,
        remote_file_key: str,
    ) -> None:
        r"""Download a file from the Amazon S3 bucket to the local system.

        Args:
            local_file_path (Path): The path to the local file to be saved.
            remote_file_key (str): The key of the object in the bucket.
        """
        file = self._client.get_object(
            Bucket=self._bucket_name,
            Key=remote_file_key,
        )
        with open(local_file_path, "wb") as f:
            f.write(file["Body"].read())

    def _object_exists(self, file_key: str) -> bool:
        r"""
        Check if the object exists in the Amazon S3 bucket.

        Args:
            file_key: The key of the object in the bucket.

        Returns:
            bool: Whether the object exists in the bucket.
        """
        try:
            self._client.head_object(Bucket=self._bucket_name, Key=file_key)
            return True
        except self._client.exceptions.ClientError:
            return False
