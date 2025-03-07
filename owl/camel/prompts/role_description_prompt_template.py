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

from camel.prompts.ai_society import AISocietyPromptTemplateDict
from camel.prompts.base import TextPrompt
from camel.types import RoleType


# flake8: noqa :E501
class RoleDescriptionPromptTemplateDict(AISocietyPromptTemplateDict):
    r"""A dictionary containing :obj:`TextPrompt` used in the `role description`
    task.

    Attributes:
        ROLE_DESCRIPTION_PROMPT (TextPrompt): A default prompt to
            describe the role descriptions.
        ASSISTANT_PROMPT (TextPrompt): A system prompt for the AI assistant
            that outlines the rules of the conversation and provides
            instructions for completing tasks.
        USER_PROMPT (TextPrompt): A system prompt for the AI user that
            outlines the rules of the conversation and provides instructions
            for giving instructions to the AI assistant.
    """

    ROLE_DESCRIPTION_PROMPT = TextPrompt(
        """===== ROLES WITH DESCRIPTION =====
{user_role} and {assistant_role} are collaborating to complete a task: {task}.
Competencies, characteristics, duties and workflows of {user_role} to complete the task: {user_description}
{assistant_role}'s competencies, characteristics, duties and workflows to complete the task: {assistant_description}
"""
    )

    ASSISTANT_PROMPT = TextPrompt(ROLE_DESCRIPTION_PROMPT + AISocietyPromptTemplateDict.ASSISTANT_PROMPT)

    USER_PROMPT = TextPrompt(ROLE_DESCRIPTION_PROMPT + AISocietyPromptTemplateDict.USER_PROMPT)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update(
            {
                "role_description": self.ROLE_DESCRIPTION_PROMPT,
                RoleType.ASSISTANT: self.ASSISTANT_PROMPT,
                RoleType.USER: self.USER_PROMPT,
            }
        )
