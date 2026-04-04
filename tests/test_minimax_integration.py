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

"""Integration tests for MiniMax model with CAMEL framework.

These tests require a valid MINIMAX_API_KEY environment variable.
They are skipped if the API key is not set.
"""

import os
import sys
import pathlib
import pytest

# Ensure project root is on the path
project_root = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
skip_no_key = pytest.mark.skipif(
    not MINIMAX_API_KEY,
    reason="MINIMAX_API_KEY not set",
)


@skip_no_key
class TestMiniMaxLiveAPI:
    """Integration tests that call the actual MiniMax API."""

    def test_simple_chat_completion(self):
        """Test a simple chat completion with MiniMax API."""
        from camel.models import ModelFactory
        from camel.agents import ChatAgent
        from camel.types import ModelPlatformType

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="MiniMax-M2.7",
            url="https://api.minimax.io/v1",
            api_key=MINIMAX_API_KEY,
            model_config_dict={"temperature": 0},
        )

        agent = ChatAgent(
            "You are a helpful assistant. Answer concisely.",
            model=model,
        )

        response = agent.step("What is 2 + 2? Reply with just the number.")
        assert response is not None
        assert response.msgs is not None
        assert len(response.msgs) > 0
        content = response.msgs[0].content
        assert "4" in content

    def test_multiple_models_creation(self):
        """Test creating multiple MiniMax model instances for different roles."""
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        models = {}
        for role in ["web", "reasoning", "coordinator"]:
            models[role] = ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
                model_type="MiniMax-M2.7",
                url="https://api.minimax.io/v1",
                api_key=MINIMAX_API_KEY,
                model_config_dict={"temperature": 0},
            )
        assert len(models) == 3
        for model in models.values():
            assert model is not None

    def test_chat_agent_with_system_prompt(self):
        """Test creating a ChatAgent with a custom system prompt using MiniMax."""
        from camel.models import ModelFactory
        from camel.agents import ChatAgent
        from camel.types import ModelPlatformType

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="MiniMax-M2.7",
            url="https://api.minimax.io/v1",
            api_key=MINIMAX_API_KEY,
            model_config_dict={"temperature": 0},
        )

        agent = ChatAgent(
            "You are a coding assistant. Always respond with Python code.",
            model=model,
        )

        response = agent.step("Write a one-line Python hello world program.")
        assert response is not None
        assert response.msgs is not None
        content = response.msgs[0].content
        assert "print" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
