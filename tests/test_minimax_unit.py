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

"""Unit tests for MiniMax model integration with OWL."""

import os
import sys
import pathlib
import importlib
from unittest.mock import patch, MagicMock
import pytest


# Ensure project root is on the path
project_root = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMiniMaxModuleConstants:
    """Test MiniMax module constants and configuration."""

    def test_minimax_api_url(self):
        """Test that MiniMax API URL is correctly defined."""
        module_path = project_root / "examples" / "run_minimax.py"
        content = module_path.read_text()
        assert 'MINIMAX_API_URL = "https://api.minimax.io/v1"' in content

    def test_minimax_model_name(self):
        """Test that MiniMax model name is correctly defined."""
        module_path = project_root / "examples" / "run_minimax.py"
        content = module_path.read_text()
        assert 'MINIMAX_MODEL = "MiniMax-M2.7"' in content

    def test_minimax_model_is_valid(self):
        """Test that the configured model name is a known MiniMax model."""
        module_path = project_root / "examples" / "run_minimax.py"
        content = module_path.read_text()
        # Extract model name from source
        import re
        match = re.search(r'MINIMAX_MODEL\s*=\s*"([^"]+)"', content)
        assert match is not None
        model_name = match.group(1)
        valid_models = [
            "MiniMax-M2.7",
            "MiniMax-M2.5",
            "MiniMax-M2.5-highspeed",
        ]
        assert model_name in valid_models


class TestMiniMaxWebappIntegration:
    """Test MiniMax integration with the webapp module selection."""

    def test_minimax_in_webapp_en_modules(self):
        """Test that run_minimax is listed in English webapp MODULE_DESCRIPTIONS."""
        sys.path.insert(0, str(project_root / "owl"))
        # Read the file directly to check for the module entry
        webapp_path = project_root / "owl" / "webapp.py"
        content = webapp_path.read_text()
        assert '"run_minimax"' in content
        assert "MiniMax" in content

    def test_minimax_in_webapp_zh_modules(self):
        """Test that run_minimax is listed in Chinese webapp MODULE_DESCRIPTIONS."""
        webapp_path = project_root / "owl" / "webapp_zh.py"
        content = webapp_path.read_text()
        assert '"run_minimax"' in content
        assert "MiniMax" in content

    def test_minimax_in_webapp_jp_modules(self):
        """Test that run_minimax is listed in Japanese webapp MODULE_DESCRIPTIONS."""
        webapp_path = project_root / "owl" / "webapp_jp.py"
        content = webapp_path.read_text()
        assert '"run_minimax"' in content
        assert "MiniMax" in content


class TestMiniMaxEnvTemplate:
    """Test MiniMax configuration in environment templates."""

    def test_minimax_api_key_in_env_template(self):
        """Test that MINIMAX_API_KEY is documented in .env_template."""
        env_template_path = project_root / "owl" / ".env_template"
        content = env_template_path.read_text()
        assert "MINIMAX_API_KEY" in content

    def test_minimax_platform_url_in_env_template(self):
        """Test that MiniMax platform URL is documented in .env_template."""
        env_template_path = project_root / "owl" / ".env_template"
        content = env_template_path.read_text()
        assert "platform.minimaxi.com" in content

    def test_minimax_in_webapp_env_template(self):
        """Test that MINIMAX_API_KEY is in webapp DEFAULT_ENV_TEMPLATE."""
        webapp_path = project_root / "owl" / "webapp.py"
        content = webapp_path.read_text()
        assert "MINIMAX_API_KEY" in content


class TestMiniMaxReadme:
    """Test MiniMax documentation in README files."""

    def test_minimax_in_readme_en(self):
        """Test that MiniMax is mentioned in English README."""
        readme_path = project_root / "README.md"
        content = readme_path.read_text()
        assert "run_minimax" in content
        assert "MiniMax" in content

    def test_minimax_in_readme_zh(self):
        """Test that MiniMax is mentioned in Chinese README."""
        readme_path = project_root / "README_zh.md"
        content = readme_path.read_text()
        assert "run_minimax" in content
        assert "MiniMax" in content


class TestMiniMaxModuleStructure:
    """Test the structure of the MiniMax example module."""

    def test_module_defines_construct_agent_list(self):
        """Test that run_minimax defines construct_agent_list function."""
        module_path = project_root / "examples" / "run_minimax.py"
        content = module_path.read_text()
        assert "def construct_agent_list()" in content

    def test_module_defines_construct_workforce(self):
        """Test that run_minimax defines construct_workforce function."""
        module_path = project_root / "examples" / "run_minimax.py"
        content = module_path.read_text()
        assert "def construct_workforce()" in content

    def test_module_defines_main(self):
        """Test that run_minimax defines main function."""
        module_path = project_root / "examples" / "run_minimax.py"
        content = module_path.read_text()
        assert "def main():" in content

    def test_module_uses_openai_compatible_platform(self):
        """Test that the module uses OPENAI_COMPATIBLE_MODEL platform type."""
        module_path = project_root / "examples" / "run_minimax.py"
        content = module_path.read_text()
        assert "ModelPlatformType.OPENAI_COMPATIBLE_MODEL" in content

    def test_module_reads_minimax_api_key(self):
        """Test that the module reads MINIMAX_API_KEY from environment."""
        module_path = project_root / "examples" / "run_minimax.py"
        content = module_path.read_text()
        assert 'os.getenv("MINIMAX_API_KEY")' in content

    def test_module_uses_temperature_zero(self):
        """Test that all models use temperature=0 for deterministic output."""
        module_path = project_root / "examples" / "run_minimax.py"
        content = module_path.read_text()
        assert '"temperature": 0' in content

    def test_module_creates_three_agents(self):
        """Test that the module creates the expected agent types."""
        module_path = project_root / "examples" / "run_minimax.py"
        content = module_path.read_text()
        assert "Web Agent" in content
        assert "Document Processing Agent" in content
        assert "Reasoning Coding Agent" in content


class TestMiniMaxModelFactory:
    """Test MiniMax model creation via CAMEL ModelFactory."""

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_model_factory_create_with_minimax(self):
        """Test that ModelFactory.create works with MiniMax configuration."""
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="MiniMax-M2.7",
            url="https://api.minimax.io/v1",
            api_key="test-key-123",
            model_config_dict={"temperature": 0},
        )
        assert model is not None

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_model_factory_create_m25(self):
        """Test that ModelFactory.create works with MiniMax-M2.5."""
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="MiniMax-M2.5",
            url="https://api.minimax.io/v1",
            api_key="test-key-123",
            model_config_dict={"temperature": 0},
        )
        assert model is not None

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_model_factory_create_m25_highspeed(self):
        """Test that ModelFactory.create works with MiniMax-M2.5-highspeed."""
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type="MiniMax-M2.5-highspeed",
            url="https://api.minimax.io/v1",
            api_key="test-key-123",
            model_config_dict={"temperature": 0},
        )
        assert model is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
