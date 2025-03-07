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
import logging
import os
import time
from typing import IO, Any, Optional, Union

import requests

from camel.utils import api_keys_required

logger = logging.getLogger(__name__)


class ChunkrReader:
    r"""Chunkr Reader for processing documents and returning content
    in various formats.

    Args:
        api_key (Optional[str], optional): The API key for Chunkr API. If not
            provided, it will be retrieved from the environment variable
            `CHUNKR_API_KEY`. (default: :obj:`None`)
        url (Optional[str], optional): The url to the Chunkr service.
            (default: :obj:`https://api.chunkr.ai/api/v1/task`)
        timeout (int, optional): The maximum time in seconds to wait for the
            API responses. (default: :obj:`30`)
        **kwargs (Any): Additional keyword arguments for request headers.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        url: Optional[str] = "https://api.chunkr.ai/api/v1/task",
        timeout: int = 30,
        **kwargs: Any,
    ) -> None:
        self._api_key = api_key or os.getenv("CHUNKR_API_KEY")
        self._url = os.getenv("CHUNKR_API_URL") or url
        self._headers = {
            "Authorization": f"{self._api_key}",
            **kwargs,
        }
        self.timeout = timeout

    def submit_task(
        self,
        file_path: str,
        model: str = "Fast",
        ocr_strategy: str = "Auto",
        target_chunk_length: str = "512",
    ) -> str:
        r"""Submits a file to the Chunkr API and returns the task ID.

        Args:
            file_path (str): The path to the file to be uploaded.
            model (str, optional): The model to be used for the task.
                (default: :obj:`Fast`)
            ocr_strategy (str, optional): The OCR strategy. Defaults to 'Auto'.
            target_chunk_length (str, optional): The target chunk length.
                (default: :obj:`512`)

        Returns:
            str: The task ID.
        """
        with open(file_path, "rb") as file:
            files: dict[str, Union[tuple[None, IO[bytes]], tuple[None, str]]] = {
                "file": (
                    None,
                    file,
                ),  # Properly pass the file as a binary stream
                "model": (None, model),
                "ocr_strategy": (None, ocr_strategy),
                "target_chunk_length": (None, target_chunk_length),
            }
            try:
                response = requests.post(
                    self._url,  # type: ignore[arg-type]
                    headers=self._headers,
                    files=files,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                task_id = response.json().get("task_id")
                if not task_id:
                    raise ValueError("Task ID not returned in the response.")
                logger.info(f"Task submitted successfully. Task ID: {task_id}")
                return task_id
            except Exception as e:
                logger.error(f"Failed to submit task: {e}")
                raise ValueError(f"Failed to submit task: {e}") from e

    def get_task_output(self, task_id: str, max_retries: int = 5) -> str:
        r"""Polls the Chunkr API to check the task status and returns the task
        result.

        Args:
            task_id (str): The task ID to check the status for.
            max_retries (int, optional): Maximum number of retry attempts.
                (default: :obj:`5`)

        Returns:
            str: The formatted task result in JSON format.

        Raises:
            ValueError: If the task status cannot be retrieved.
            RuntimeError: If the maximum number of retries is reached without
                a successful task completion.
        """
        url_get = f"{self._url}/{task_id}"
        attempts = 0

        while attempts < max_retries:
            try:
                response = requests.get(url_get, headers=self._headers, timeout=self.timeout)
                response.raise_for_status()
                task_status = response.json().get("status")

                if task_status == "Succeeded":
                    logger.info(f"Task {task_id} completed successfully.")
                    return self._pretty_print_response(response.json())
                else:
                    logger.info(f"Task {task_id} is still {task_status}. Retrying " "in 5 seconds...")
            except Exception as e:
                logger.error(f"Failed to retrieve task status: {e}")
                raise ValueError(f"Failed to retrieve task status: {e}") from e

            attempts += 1
            time.sleep(5)

        logger.error(f"Max retries reached for task {task_id}.")
        raise RuntimeError(f"Max retries reached for task {task_id}.")

    def _pretty_print_response(self, response_json: dict) -> str:
        r"""Pretty prints the JSON response.

        Args:
            response_json (dict): The response JSON to pretty print.

        Returns:
            str: Formatted JSON as a string.
        """
        return json.dumps(response_json, indent=4)
