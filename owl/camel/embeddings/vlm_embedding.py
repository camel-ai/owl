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
from typing import Any, List, Optional, Union

from PIL import Image

from camel.embeddings import BaseEmbedding
from camel.logger import get_logger

logger = get_logger(__name__)


class VisionLanguageEmbedding(BaseEmbedding[Union[str, Image.Image]]):
    r"""Provides image embedding functionalities using multimodal model.

    Args:
        model_name : The model type to be used for generating embeddings.
            And the default value is: obj:`openai/clip-vit-base-patch32`.

    Raises:
        RuntimeError: If an unsupported model type is specified.
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32") -> None:
        r"""Initializes the: obj: `VisionLanguageEmbedding` class with a
        specified model and return the dimension of embeddings.

        Args:
            model_name (str, optional): The version name of the model to use.
                (default: :obj:`openai/clip-vit-base-patch32`)
        """
        from transformers import AutoModel, AutoProcessor

        try:
            self.model = AutoModel.from_pretrained(model_name)
            self.processor = AutoProcessor.from_pretrained(model_name)
        except Exception as e:
            raise RuntimeError(f"Failed to load model '{model_name}': {e}")

        self.valid_processor_kwargs = []
        self.valid_model_kwargs = []

        try:
            self.valid_processor_kwargs = self.processor.image_processor._valid_processor_keys
            self.valid_model_kwargs = [
                "pixel_values",
                "return_dict",
                "interpolate_pos_encoding",
            ]
        except Exception:
            logger.warning("not typically processor and model structure")
            pass
        self.dim: Optional[int] = None

    def embed_list(self, objs: List[Union[Image.Image, str]], **kwargs: Any) -> List[List[float]]:
        """Generates embeddings for the given images or texts.

        Args:
            objs (List[Image.Image|str]): The list of images or texts for
                which to generate the embeddings.
            image_processor_kwargs: Extra kwargs passed to the image processor.
            tokenizer_kwargs: Extra kwargs passed to the text tokenizer
                (processor).
            model_kwargs: Extra kwargs passed to the main model.

        Returns:
            List[List[float]]: A list that represents the generated embedding
                as a list of floating-point numbers.

        Raises:
            ValueError: If the input type is not `Image.Image` or `str`.
        """
        if not objs:
            raise ValueError("Input objs list is empty.")

        image_processor_kwargs: Optional[dict] = kwargs.get("image_processor_kwargs", {})
        tokenizer_kwargs: Optional[dict] = kwargs.get("tokenizer_kwargs", {})
        model_kwargs: Optional[dict] = kwargs.get("model_kwargs", {})

        result_list = []
        for obj in objs:
            if isinstance(obj, Image.Image):
                image_input = self.processor(
                    images=obj,
                    return_tensors="pt",
                    padding=True,
                    **image_processor_kwargs,
                )
                image_feature = (
                    self.model.get_image_features(**image_input, **model_kwargs).squeeze(dim=0).tolist()
                )
                result_list.append(image_feature)
            elif isinstance(obj, str):
                text_input = self.processor(
                    text=obj,
                    return_tensors="pt",
                    padding=True,
                    **tokenizer_kwargs,
                )
                text_feature = self.model.get_text_features(**text_input, **model_kwargs).squeeze(dim=0).tolist()
                result_list.append(text_feature)
            else:
                raise ValueError("Input type is not image nor text.")

        self.dim = len(result_list[0])

        if any(len(result) != self.dim for result in result_list):
            raise ValueError("Dimensionality is not consistent.")

        return result_list

    def get_output_dim(self) -> int:
        r"""Returns the output dimension of the embeddings.

        Returns:
            int: The dimensionality of the embedding for the current model.
        """
        if self.dim is None:
            text = "dimension"
            inputs = self.processor(text=[text], return_tensors="pt")
            self.dim = self.model.get_text_features(**inputs).shape[1]
        return self.dim
