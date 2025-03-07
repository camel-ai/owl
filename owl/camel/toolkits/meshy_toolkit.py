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
from typing import Any, Dict

import requests

from camel.toolkits.base import BaseToolkit
from camel.utils import api_keys_required


class MeshyToolkit(BaseToolkit):
    r"""A class representing a toolkit for 3D model generation using Meshy.

    This class provides methods that handle text/image to 3D model
    generation using Meshy.

    Call the generate_3d_model_complete method to generate a refined 3D model.

    Ref:
    https://docs.meshy.ai/api-text-to-3d-beta#create-a-text-to-3d-preview-task
    """

    @api_keys_required("MESHY_API_KEY")
    def __init__(self):
        r"""Initializes the MeshyToolkit with the API key from the
        environment.
        """
        self.api_key = os.getenv("MESHY_API_KEY")

    def generate_3d_preview(self, prompt: str, art_style: str, negative_prompt: str) -> Dict[str, Any]:
        r"""Generates a 3D preview using the Meshy API.

        Args:
            prompt (str): Description of the object.
            art_style (str): Art style for the 3D model.
            negative_prompt (str): What the model should not look like.

        Returns:
            Dict[str, Any]: The result property of the response contains the
                task id of the newly created Text to 3D task.
        """
        payload = {
            "mode": "preview",
            "prompt": prompt,
            "art_style": art_style,
            "negative_prompt": negative_prompt,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = requests.post(
            "https://api.meshy.ai/v2/text-to-3d",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def refine_3d_model(self, preview_task_id: str) -> Dict[str, Any]:
        r"""Refines a 3D model using the Meshy API.

        Args:
            preview_task_id (str): The task ID of the preview to refine.

        Returns:
            Dict[str, Any]: The response from the Meshy API.
        """
        payload = {"mode": "refine", "preview_task_id": preview_task_id}
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = requests.post(
            "https://api.meshy.ai/v2/text-to-3d",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        r"""Retrieves the status or result of a specific 3D model generation
        task using the Meshy API.

        Args:
            task_id (str): The ID of the task to retrieve.

        Returns:
            Dict[str, Any]: The response from the Meshy API.
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = requests.get(
            f"https://api.meshy.ai/v2/text-to-3d/{task_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def wait_for_task_completion(
        self, task_id: str, polling_interval: int = 10, timeout: int = 3600
    ) -> Dict[str, Any]:
        r"""Waits for a task to complete by polling its status.

        Args:
            task_id (str): The ID of the task to monitor.
            polling_interval (int): Seconds to wait between status checks.
                (default::obj:`10`)
            timeout (int): Maximum seconds to wait before timing out.
                (default::obj:`3600`)

        Returns:
            Dict[str, Any]: Final response from the API when task completes.

        Raises:
            TimeoutError: If task doesn't complete within timeout period.
            RuntimeError: If task fails or is canceled.
        """
        import time

        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")

            response = self.get_task_status(task_id)
            status = response.get("status")  # Direct access to status field
            elapsed = int(time.time() - start_time)

            print(f"Status after {elapsed}s: {status}")

            if status == "SUCCEEDED":
                return response
            elif status in [
                "FAILED",
                "CANCELED",
            ]:  # Also updating these status values
                raise RuntimeError(f"Task {task_id} {status}")

            time.sleep(polling_interval)

    def generate_3d_model_complete(self, prompt: str, art_style: str, negative_prompt: str) -> Dict[str, Any]:
        r"""Generates a complete 3D model by handling preview and refinement
        stages

        Args:
            prompt (str): Description of the object.
            art_style (str): Art style for the 3D model.
            negative_prompt (str): What the model should not look like.

        Returns:
            Dict[str, Any]: The final refined 3D model response.
        """
        # Generate preview
        preview_response = self.generate_3d_preview(prompt, art_style, negative_prompt)
        preview_task_id = str(preview_response.get("result"))

        # Wait for preview completion
        self.wait_for_task_completion(preview_task_id)

        # Start refinement
        refine_response = self.refine_3d_model(preview_task_id)
        refine_task_id = str(refine_response.get("result"))

        # Wait for refinement completion and return final result
        return self.wait_for_task_completion(refine_task_id)
