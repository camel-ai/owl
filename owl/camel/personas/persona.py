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
import uuid
from typing import ClassVar, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from camel.prompts import PersonaHubPrompt, TextPrompt


class Persona(BaseModel):
    r"""A persona is a character in the society.

    Attributes:
        name (Optional[str]): Name of the persona.
        description (Optional[str]): Description of the persona.
        text_to_persona_prompt (Union[TextPrompt, str]): The prompt to convert
            text into a persona.
        persona_to_persona_prompt (Union[TextPrompt, str]): Persona-to-Persona
            interaction prompt.
        id (uuid.UUID): The unique identifier for the persona, automatically
            generated.
        _id (uuid.UUID): Internal unique identifier for the persona,
            generated lazily using `uuid.uuid4`.
        model_config (ClassVar[ConfigDict]): Configuration for the Pydantic
            model. Allows arbitrary types and includes custom JSON schema
            settings.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    _id: uuid.UUID = PrivateAttr(default_factory=uuid.uuid4)

    # Field with default_factory to avoid circular import issues
    # Union type allows either TextPrompt or str
    text_to_persona_prompt: Union[TextPrompt, str] = Field(
        default_factory=lambda: PersonaHubPrompt.TEXT_TO_PERSONA,
        description="Text to Persona Prompt",
    )

    # Similar to text_to_persona_prompt, using default_factory for lazy
    # evaluation
    persona_to_persona_prompt: Union[TextPrompt, str] = Field(
        default_factory=lambda: PersonaHubPrompt.PERSONA_TO_PERSONA,
        description="Persona to Persona Prompt",
    )

    # Class-level configuration for Pydantic model
    # ClassVar indicates this is a class variable, not an instance variable
    model_config: ClassVar[ConfigDict] = ConfigDict(
        # Allow the use of custom types TextPrompt
        arbitrary_types_allowed=True,
        # Custom JSON schema configuration
        json_schema_extra={
            "properties": {
                # Ensure text_to_persona_prompt and persona_to_persona_prompt
                # are treated as strings in JSON schema
                "text_to_persona_prompt": {"type": "string"},
                "persona_to_persona_prompt": {"type": "string"},
            }
        },
    )

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @classmethod
    def model_json_schema(cls):
        schema = super().schema()
        schema["properties"]["id"] = {"type": "string", "format": "uuid"}
        return schema

    def dict(self, *args, **kwargs):
        # Output: {'name': 'Alice', 'description': None, 'text_to_persona_prompt': '...', 'persona_to_persona_prompt': '...', 'id': 'f47ac10b-58cc-4372-a567-0e02b2c3d479'}  # noqa: E501
        d = super().model_dump(*args, **kwargs)
        d["id"] = str(self.id)
        return d

    def json(self, *args, **kwargs):
        # Output: '{"name": "Alice", "description": null, "text_to_persona_prompt": "...", "persona_to_persona_prompt": "...", "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"}'  # noqa: E501
        d = self.dict(*args, **kwargs)
        return json.dumps(
            d,
            indent=4,  # Pretty-print with 4 spaces indentation
            sort_keys=True,  # Sort keys alphabetically
            separators=(
                ",",
                ": ",
            ),  # Fine-tune separators for better readability
        )
