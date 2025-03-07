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

from typing import Any

from camel.prompts.base import TextPrompt, TextPromptDict


class PersonaHubPrompt(TextPromptDict):
    r"""A dictionary containing :obj:`TextPrompt` used for generating and
    relating personas based on given text or existing personas.

    This class inherits from TextPromptDict, allowing for easy access and
    management of the prompts.

    Attributes:
        TEXT_TO_PERSONA (TextPrompt): A prompt for inferring a persona from a
            given text. This prompt asks to identify who is likely to interact
            with the provided text in various ways (read, write, like,
            dislike). The response should follow a specific template format.

        PERSONA_TO_PERSONA (TextPrompt): A prompt for deriving related personas
            based on a given persona. This prompt asks to describe personas who
            might have a close relationship with the provided persona. The
            response should follow a specific template format, allowing for
            multiple related personas.
    """

    TEXT_TO_PERSONA = TextPrompt(
        """
Who is likely to {action} the following text? Provide a detailed and specific persona description.

Text: {text}
"""
    )  # noqa: E501

    PERSONA_TO_PERSONA = TextPrompt(
        """
Given the following persona: 
{persona_name}
{persona_description}

Who is likely to be in a close relationship with this persona? Describe the related personas and their relationships.
"""
    )  # noqa: E501

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update(
            {
                "text_to_persona": self.TEXT_TO_PERSONA,
                "persona_to_persona": self.PERSONA_TO_PERSONA,
            }
        )
