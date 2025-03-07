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
import re
from typing import Dict, Optional, Union

from camel.agents.chat_agent import ChatAgent
from camel.messages import BaseMessage
from camel.models import BaseModelBackend
from camel.prompts import TextPrompt
from camel.types import RoleType

# AgentOps decorator setting
try:
    import os

    if os.getenv("AGENTOPS_API_KEY") is not None:
        from agentops import track_agent
    else:
        raise ImportError
except (ImportError, AttributeError):
    from camel.utils import track_agent


@track_agent(name="RoleAssignmentAgent")
class RoleAssignmentAgent(ChatAgent):
    r"""An agent that generates role names based on the task prompt.

    Args:
        model (BaseModelBackend, optional): The model backend to use for
            generating responses. (default: :obj:`OpenAIModel` with
            `GPT_4O_MINI`)

    Attributes:
        role_assignment_prompt (TextPrompt): A prompt for the agent to generate
        role names.
    """

    def __init__(
        self,
        model: Optional[BaseModelBackend] = None,
    ) -> None:
        system_message = BaseMessage(
            role_name="Role Assigner",
            role_type=RoleType.ASSISTANT,
            meta_dict=None,
            content="You assign roles based on tasks.",
        )
        super().__init__(system_message, model=model)

    def run(
        self,
        task_prompt: Union[str, TextPrompt],
        num_roles: int = 2,
    ) -> Dict[str, str]:
        r"""Generate role names based on the input task prompt.

        Args:
            task_prompt (Union[str, TextPrompt]): The prompt
                for the task based on which the roles are to be generated.
            num_roles (int, optional): The number of roles to generate.
                (default: :obj:`2`)

        Returns:
            Dict[str, str]: A dictionary mapping role names to their
                descriptions.
        """
        self.reset()

        expert_prompt = "===== ANSWER PROMPT =====\n" + "\n".join(
            f"Domain expert {i + 1}: <BLANK>\n"
            f"Associated competencies, characteristics, duties "
            f"and workflows: <BLANK>. End."
            for i in range(num_roles or 0)
        )
        role_assignment_generation_prompt = TextPrompt(
            "You are a role assignment agent, and you're in charge of "
            + "recruiting {num_roles} experts for the following task."
            + "\n==== TASK =====\n {task}\n\n"
            + "Identify the domain experts you'd recruit and detail their "
            + "associated competencies, characteristics, duties and workflows "
            + "to complete the task.\n "
            + "Your answer MUST adhere to the format of ANSWER PROMPT, and "
            + "ONLY answer the BLANKs.\n"
            + expert_prompt
        )
        role_assignment_generation = role_assignment_generation_prompt.format(
            num_roles=num_roles, task=task_prompt
        )

        role_assignment_generation_msg = BaseMessage.make_user_message(
            role_name="Role Assigner", content=role_assignment_generation
        )

        response = self.step(input_message=role_assignment_generation_msg)

        msg = response.msg  # type: BaseMessage
        terminated = response.terminated

        # Distribute the output completions into role names and descriptions
        role_names = [
            desc.replace("<|", "").replace("|>", "")
            for desc in re.findall(
                r"Domain expert \d: (.+?)\nAssociated competencies,",
                msg.content,
                re.DOTALL,
            )
        ]
        role_descriptions = [
            desc.replace("<|", "").replace("|>", "")
            for desc in re.findall(
                r"Associated competencies, characteristics, " r"duties and workflows: (.+?) End.",
                msg.content,
                re.DOTALL,
            )
        ]

        if len(role_names) != num_roles or len(role_descriptions) != num_roles:
            raise RuntimeError("Got None or insufficient information of roles.")
        if terminated:
            raise RuntimeError("Role assignment failed.")

        role_descriptions_dict = {
            role_name: description for role_name, description in zip(role_names, role_descriptions)
        }

        return role_descriptions_dict
