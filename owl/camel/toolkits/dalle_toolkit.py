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
import base64
import os
import uuid
from io import BytesIO
from typing import List, Optional

from openai import OpenAI
from PIL import Image

from camel.toolkits import FunctionTool
from camel.toolkits.base import BaseToolkit


class DalleToolkit(BaseToolkit):
    r"""A class representing a toolkit for image generation using OpenAI's
    DALL-E model.
    """

    def base64_to_image(self, base64_string: str) -> Optional[Image.Image]:
        r"""Converts a base64 encoded string into a PIL Image object.

        Args:
            base64_string (str): The base64 encoded string of the image.

        Returns:
            Optional[Image.Image]: The PIL Image object or None if conversion
                fails.
        """
        try:
            # Decode the base64 string to get the image data
            image_data = base64.b64decode(base64_string)
            # Create a memory buffer for the image data
            image_buffer = BytesIO(image_data)
            # Open the image using the PIL library
            image = Image.open(image_buffer)
            return image
        except Exception as e:
            print(f"An error occurred while converting base64 to image: {e}")
            return None

    def image_path_to_base64(self, image_path: str) -> str:
        r"""Converts the file path of an image to a Base64 encoded string.

        Args:
            image_path (str): The path to the image file.

        Returns:
            str: A Base64 encoded string representing the content of the image
                file.
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"An error occurred while converting image path to base64: {e}")
            return ""

    def image_to_base64(self, image: Image.Image) -> str:
        r"""Converts an image into a base64-encoded string.

        This function takes an image object as input, encodes the image into a
        PNG format base64 string, and returns it.
        If the encoding process encounters an error, it prints the error
        message and returns None.

        Args:
            image: The image object to be encoded, supports any image format
                that can be saved in PNG format.

        Returns:
            str: A base64-encoded string of the image.
        """
        try:
            with BytesIO() as buffered_image:
                image.save(buffered_image, format="PNG")
                buffered_image.seek(0)
                image_bytes = buffered_image.read()
                base64_str = base64.b64encode(image_bytes).decode("utf-8")
                return base64_str
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""

    def get_dalle_img(self, prompt: str, image_dir: str = "img") -> str:
        r"""Generate an image using OpenAI's DALL-E model.
            The generated image is saved to the specified directory.

        Args:
            prompt (str): The text prompt based on which the image is
                generated.
            image_dir (str): The directory to save the generated image.
                Defaults to 'img'.

        Returns:
            str: The path to the saved image.
        """

        dalle_client = OpenAI()
        response = dalle_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792",
            quality="standard",
            n=1,  # NOTE: now dall-e-3 only supports n=1
            response_format="b64_json",
        )
        image_b64 = response.data[0].b64_json
        image = self.base64_to_image(image_b64)  # type: ignore[arg-type]

        if image is None:
            raise ValueError("Failed to convert base64 string to image.")

        os.makedirs(image_dir, exist_ok=True)
        image_path = os.path.join(image_dir, f"{uuid.uuid4()}.png")
        image.save(image_path)

        return image_path

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """
        return [FunctionTool(self.get_dalle_img)]
