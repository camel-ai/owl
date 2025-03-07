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
import logging
import json
from PIL import Image
from typing import List, Literal, Tuple
from urllib.parse import urlparse

from camel.agents import ChatAgent
from camel.configs import ChatGPTConfig
from camel.toolkits.base import BaseToolkit
from camel.toolkits import FunctionTool, CodeExecutionToolkit
from camel.types import ModelType, ModelPlatformType
from camel.models import ModelFactory, OpenAIModel
from camel.messages import BaseMessage

logger = logging.getLogger(__name__)


class ImageAnalysisToolkit(BaseToolkit):
    r"""A class representing a toolkit for image comprehension operations.

    This class provides methods for understanding images, such as identifying
    objects, text in images.
    """

    def __init__(self, model: Literal["gpt-4o", "gpt-4o-mini"] = "gpt-4o"):
        self.model_type = ModelType.GPT_4O
        if model == "gpt-4o":
            self.model_type = ModelType.GPT_4O
        elif model == "gpt-4o-mini":
            self.model_type = ModelType.GPT_4O_MINI
        else:
            raise ValueError(f"Invalid model type: {model}")

    def _construct_image_url(self, image_path: str) -> str:
        parsed_url = urlparse(image_path)
        is_url = all([parsed_url.scheme, parsed_url.netloc])

        image_url = image_path

        if not is_url:
            image_url = f"data:image/jpeg;base64,{self._encode_image(image_path)}"
        return image_url

    def _encode_image(self, image_path: str):
        r"""Encode an image by its image path.

        Arg:
            image_path (str): The path to the image file."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _judge_if_write_code(self, question: str, image_path: str) -> Tuple[bool, str]:

        _image_url = self._construct_image_url(image_path)

        prompt = f"""
        Given the question <question>{question}</question>, do you think it is suitable to write python code (using libraries like cv2) to process the image to get the answer?
        Your output should be in json format (```json ```) including the following fields:
        - `image_caption`: str, A detailed caption about the image. If it is suitable for writing code, it should contains helpful instructions and necessary informations for how to writing code.
        - `if_write_code`: bool, True if it is suitable to write code to process the image, False otherwise.
        """

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant for image relevant tasks, and can judge whether \
                the given image is suitable for writing code to process or not. ",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": _image_url,
                        },
                    },
                ],
            },
        ]

        LLM = OpenAIModel(model_type=self.model_type)
        resp = LLM.run(messages)

        result_str = resp.choices[0].message.content.lower()
        result_str = result_str.replace("```json", "").replace("```", "").strip()

        result_dict = json.loads(result_str)

        if_write_code = result_dict.get("if_write_code", False)
        image_caption = result_dict.get("image_caption", "")

        return if_write_code, image_caption

    def _get_image_caption(self, image_path: str) -> str:

        _image_url = self._construct_image_url(image_path)

        prompt = f"""
        Please make a detailed description about the image.
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": _image_url,
                        },
                    },
                ],
            },
        ]

        LLM = OpenAIModel(model_type=self.model_type)
        resp = LLM.run(messages)

        return resp.choices[0].message.content

    def ask_question_about_image(self, image_path: str, question: str) -> str:
        r"""Ask a question about the image based on the image path.

        Args:
            image_path (str): The path to the image file.
            question (str): The question to ask about the image.

        Returns:
            str: The answer to the question based on the image.
        """
        logger.debug(
            f"Calling ask_question_about_image with question: `{question}` and \
            image_path: `{image_path}`"
        )
        parsed_url = urlparse(image_path)
        is_url = all([parsed_url.scheme, parsed_url.netloc])

        if not (image_path.endswith(".jpg") or image_path.endswith(".jpeg") or image_path.endswith(".png")):
            logger.warning(
                f"The image path `{image_path}` is not a valid image path. " f"Please provide a valid image path."
            )
            return f"The image path `{image_path}` is not a valid image path."

        # _image_url = image_path

        # if not is_url:
        #     _image_url = (
        #         f"data:image/jpeg;base64,{self._encode_image(image_path)}"
        #     )

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=self.model_type,
        )

        code_model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.O3_MINI,
        )

        code_execution_toolkit = CodeExecutionToolkit(require_confirm=False, sandbox="subprocess", verbose=True)

        image_agent = ChatAgent(
            "You are a helpful assistant for image relevant tasks. Given a question related to the image, you can carefully check the image in detail and answer the question.",
            model,
        )

        code_agent = ChatAgent(
            "You are an expert of writing code to process special images leveraging libraries like cv2.",
            code_model,
            tools=code_execution_toolkit.get_tools(),
        )

        if not is_url:
            image_object = Image.open(image_path)
        else:
            import requests
            from io import BytesIO

            url_image = requests.get(image_path)
            image_object = Image.open(BytesIO(url_image.content))

        # if_write_code, image_caption = self._judge_if_write_code(question, image_path)

        # if if_write_code:
        #     prompt = f"""
        #     Please write and execute python code (for example, using cv2 library) to process the image and complete the task: {question}
        #     Here are the image path you need to process: {image_path}
        #     Here are the caption about the image: <image_caption>{image_caption}</image_caption>
        #     """
        #     message = BaseMessage.make_user_message(
        #         role_name='user',
        #         content=prompt,
        #     )
        #     resp = code_agent.step(message)
        #     return resp.msgs[0].content

        # else:
        prompt = question
        message = BaseMessage.make_user_message(role_name="user", content=prompt, image_list=[image_object])

        resp = image_agent.step(message)
        return resp.msgs[0].content

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the functions
        in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects representing the
                functions in the toolkit.
        """
        return [
            FunctionTool(self.ask_question_about_image),
        ]
