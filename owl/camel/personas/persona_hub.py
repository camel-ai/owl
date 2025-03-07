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
import ast
import re
import uuid
from functools import lru_cache
from typing import Dict, List, Literal, Optional, Union

import numpy as np
from pydantic import BaseModel, Field

from camel.agents import ChatAgent
from camel.embeddings import BaseEmbedding
from camel.models import BaseModelBackend
from camel.personas import Persona
from camel.prompts import TextPrompt


# Set structured output schema
class PersonaResponse(BaseModel):
    persona_name: str = Field(description="The name of the persona")
    persona_description: str = Field(description="The description of the persona.")


class PersonaHub:
    r"""The PersonaHub adapted from `"Scaling Synthetic Data Creation with 1,
    000,000,000 Personas"
    <https://github.com/tencent-ailab/persona-hub>`_.

    PersonaHub proposes a novel persona-driven data synthesis methodology
    that leverages various perspectives within a large language model (LLM) to
    create diverse synthetic data. By showcasing PersonaHub's use cases in
    synthesizing high-quality mathematical and logical reasoning problems,
    instructions (i.e., user prompts), knowledge-rich texts, game NPCs and
    tools (functions) at scale, the authors demonstrate persona-driven data
    synthesis is versatile, scalable, flexible, and easy to use, potentially
    driving a paradigm shift in synthetic data creation and applications in
    practice, which may have a profound impact on LLM research and development.
    Please refer to the paper for more details: https://arxiv.org/pdf/2406.20094.

    Args:
        model (BaseModelBackend, optional): The model to use for persona
            generation and manipulation. (default: :obj:`None`)
    """

    def __init__(
        self,
        model: Optional[BaseModelBackend] = None,
    ):
        self.model = model
        self.personas: Dict[uuid.UUID, Persona] = {}

    def __setitem__(self, persona: Persona):
        r"""Add a persona to the group.

        Args:
            persona (Persona): The persona to add.
        """
        self.personas[persona.id] = persona

    def __delitem__(self, persona_id: uuid.UUID):
        r"""Remove a persona from the group by ID.

        Args:
            persona_id (uuid.UUID): The ID of the persona to remove.
        """
        if persona_id in self.personas:
            del self.personas[persona_id]
        else:
            raise KeyError("Persona ID not found.")

    def __getitem__(self, persona_id: uuid.UUID) -> Persona:
        r"""Get a persona by ID.

        Args:
            persona_id (uuid.UUID): The ID of the persona to retrieve.
        """
        if persona_id in self.personas:
            return self.personas[persona_id]
        else:
            raise KeyError("Persona ID not found.")

    def text_to_persona(
        self,
        text: str,
        action: Literal["read", "write", "like", "dislike"] = "read",
    ) -> Persona:
        r"""Infers a specific persona who is likely to [read|write|like|dislike
        |...] the given text.

        Args:
            text (str): The input text for which to infer a persona.
            action (str): The action associated with the persona (default is
                "read").

        Returns:
            Persona: The inferred persona.
        """
        persona = Persona()

        text_to_persona_prompt: Union[TextPrompt, str] = persona.text_to_persona_prompt
        text_to_persona_prompt_instruction = text_to_persona_prompt.format(action=action, text=text)

        # Set Agent to generate personal
        t2p_agent = ChatAgent(system_message="You are a helpful assistant", model=self.model)
        t2p_agent.reset()

        # Get output from agent
        try:
            response = t2p_agent.step(
                text_to_persona_prompt_instruction,
                response_format=PersonaResponse,  # type: ignore[arg-type]
            )
            parsed_content = ast.literal_eval(response.msg.content)
            persona.name = parsed_content["persona_name"]
            persona.description = parsed_content["persona_description"]
        except Exception as e:
            raise RuntimeError(f"Text to persona step failed: {e}")

        return persona

    def persona_to_persona(self, persona: Persona) -> Dict[uuid.UUID, Persona]:
        r"""Derives additional personas based on interpersonal relationships
        from this persona.

        Args:
            persona (Persona): The persona from which to derive related
                personas.

        Returns:
            Dict[uuid.UUID, Persona]: A dictionary of related personas.
        """
        persona_to_persona_prompt: Union[TextPrompt, str] = persona.persona_to_persona_prompt
        answer_template = """
You MUST answer the question according to the format of the ANSWER TEMPLATE, and you can only modify the content within <BLANK>.
===== ANSWER TEMPLATE =====
1. persona_name: <BLANK>
persona_description: <BLANK>
...
n. persona_name: <BLANK>
persona_description: <BLANK>
"""  # noqa: E501
        persona_to_persona_prompt_instruction = (
            persona_to_persona_prompt.format(
                persona_name=persona.name,
                persona_description=persona.description,
            )
            + answer_template
        )

        p2p_agent = ChatAgent(system_message="You're a helpful assistant.", model=self.model)
        p2p_agent.reset()

        # Get output from agent
        try:
            response = p2p_agent.step(persona_to_persona_prompt_instruction)  # type: ignore[arg-type]
            # Structured output (TODO: Use a more robust parser)
            pattern = r"(\d+)\.\s*persona_name:\s*(.*?)\s*persona_description:\s*(.*?)\s*(?=\d+\.|$)"  # noqa: E501
            matches = re.findall(pattern, response.msg.content, re.DOTALL)

            personas: Dict[uuid.UUID, Persona] = {}
            for match in matches:
                name = match[1].strip()
                description = match[2].strip()
                new_persona = Persona(name=name, description=description)
                personas[new_persona.id] = new_persona
        except Exception as e:
            raise RuntimeError(f"Persona to persona step failed: {e}")

        return personas

    def deduplicate(
        self,
        embedding_model: Optional[BaseEmbedding] = None,
        similarity_threshold: float = 0.85,
    ) -> None:
        r"""Remove similar personas from the group.

        Args:
            embedding_model (BaseEmbedding): The embedding model
                for similarity compairsion. (default is `None`).
            similarity_threshold (float): The similarity threshold for
                deduplication (default is `0.85`).
        """
        # Changed to default similarity threshold to 0.85 as the default
        # text-embedding-3-small model may give lower similarities than others
        # This is a simplified version. Need to implement a more
        # sophisticated deduplication algorithm as described in the paper.
        if not embedding_model:
            from camel.embeddings import OpenAIEmbedding

            embedding_model = OpenAIEmbedding()
        unique_personas: Dict[uuid.UUID, Persona] = {}
        for persona_id, persona in self.personas.items():
            if not any(
                self._is_similar(persona, up, similarity_threshold, embedding_model)
                for up in unique_personas.values()
            ):
                unique_personas[persona_id] = persona
        self.personas = unique_personas

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_embedding(embedding_model: BaseEmbedding, description: Optional[str]) -> list[float]:
        r"""Cache embeddings to reduce recomputation."""
        return embedding_model.embed(description)

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        r"""Copmute the cosine similarity of two vectors.

        Args:
            vec1 (np.ndarray): Vector 1
            vec2 (np.ndarray): Vector 2
        """
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def _is_similar(
        self,
        persona1: Persona,
        persona2: Persona,
        similarity_threshold: float,
        embedding_model: BaseEmbedding,
    ) -> bool:
        r"""Check if two personas are similar by consine similarity
        of the embeddings of their descriptions.

        Args:
            persona1 (Persona1): A persona.
            persona2 (Persona2): The other persona.
            similarity_threshold (float): The threshold on consine similarity
                to determine whether the two personas are similar.
            embedding_model (BaseEmbedding): The embedding model
                for similarity compairsion.
        """

        # Ensure persona descriptions are not None
        persona1_description = persona1.description or ""
        persona2_description = persona2.description or ""

        persona1_embeddings = self._get_embedding(embedding_model, persona1_description)
        persona2_embeddings = self._get_embedding(embedding_model, persona2_description)

        similarity = self._cosine_similarity(np.array(persona1_embeddings), np.array(persona2_embeddings))

        return similarity >= similarity_threshold

    def __len__(self):
        return len(self.personas)

    def __iter__(self):
        return iter(self.personas.values())

    def get_all_personas(self) -> List[Persona]:
        r"""Return a list of all personas."""
        return list(self.personas.values())
