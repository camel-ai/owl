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
import asyncio
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.toolkits import FunctionTool
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level
from camel.toolkits import MCPToolkit

from owl.utils.enhanced_role_playing import OwlRolePlaying, arun_society

import pathlib

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")

# AI/ML Engineer Job Description
AI_ENGINEER_JOB_DESCRIPTION = """
# AI/ML Engineer Job Description

## About the Role
We are seeking a skilled AI/ML Engineer to join our team. The ideal candidate will design, develop, and deploy machine learning models and AI systems that solve complex business problems. You will work closely with cross-functional teams to understand requirements, implement solutions, and continuously improve our AI capabilities.

## Key Responsibilities
- Design, develop, and implement machine learning models and algorithms
- Build and maintain scalable ML pipelines for data processing, model training, and inference
- Collaborate with product teams to understand requirements and translate them into technical solutions
- Optimize existing models for performance, accuracy, and efficiency
- Stay current with the latest AI/ML research and technologies
- Implement and deploy models to production environments
- Monitor and troubleshoot deployed models

## Required Qualifications
- Bachelor's or Master's degree in Computer Science, AI, Machine Learning, or related field
- 3+ years of experience in machine learning or AI development
- Strong programming skills in Python and familiarity with ML frameworks (TensorFlow, PyTorch, etc.)
- Experience with deep learning architectures (CNNs, RNNs, Transformers)
- Knowledge of NLP, computer vision, or other specialized AI domains
- Experience with cloud platforms (AWS, GCP, Azure) and MLOps tools
- Strong problem-solving skills and attention to detail
- Excellent communication and collaboration abilities

## Preferred Qualifications
- PhD in Machine Learning, AI, or related field
- Experience with large language models (LLMs) and generative AI
- Contributions to open-source ML/AI projects
- Experience with distributed computing and big data technologies
- Published research in AI/ML conferences or journals
- Experience with model optimization techniques (quantization, pruning, distillation)
"""

async def construct_society(
    resume_dir: str,
    tools: List[FunctionTool],
) -> OwlRolePlaying:
    r"""build a multi-agent OwlRolePlaying instance.

    Args:
        question (str): The question to ask.
        tools (List[FunctionTool]): The MCP tools to use.
    """
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.QWEN,
            model_type=ModelType.QWEN_MAX,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.QWEN,
            model_type=ModelType.QWEN_MAX,
            model_config_dict={"temperature": 0},
        ),
    }

    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {
        "model": models["assistant"],
        "tools": tools,
    }

    task_prompt = f"""
    You are a professional resume analyzer for AI/ML Engineer positions. Your task is to:

    1. Analyze all resume files in the directory: {resume_dir}
    2. Please note when you retrieve the content of PDF files using the `pdf-reader` tool, the path is mapping to the `/pdfs` directory inside the pdf-reader docker container.
    3. For each resume, evaluate how well the candidate matches the following job description:

    {AI_ENGINEER_JOB_DESCRIPTION}

    4. Score each resume on a scale of 1-100 based on:
       - Technical skills match (40%)
       - Experience relevance (30%)
       - Education and qualifications (20%)
       - Communication and presentation (10%)

    5. Rank all candidates from most to least qualified
    6. For each candidate, highlight their strengths and areas for improvement
    7. Output your analysis to a markdown file named './resume_analysis.md' with the following sections:
       - Executive Summary
       - Individual Candidate Assessments (with scores)
       - Ranked List of Candidates
       - Recommendations for Hiring Manager

    Be thorough, fair, and objective in your assessment.
    Always execute the MCP tools, don't ask me for confirmation.
    """

    society = OwlRolePlaying(
        task_prompt=task_prompt,
        with_task_specify=False,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )
    return society


async def main():
    config_path = Path(__file__).parent / "mcp_servers_config.json"
    mcp_toolkit = MCPToolkit(config_path=str(config_path))

    try:
        await mcp_toolkit.connect()

        # Default resume directory if none provided
        default_resume_dir = "./resumes/"
    
        # Get resume directory from command line argument if provided
        resume_dir = sys.argv[1] if len(sys.argv) > 1 else default_resume_dir
    
        print(f"\033[94mAnalyzing resumes for AI/ML Engineer position...\033[0m")

        # Connect to all MCP toolkits
        tools = [*mcp_toolkit.get_tools()]
        society = await construct_society(resume_dir, tools)
        answer, chat_history, token_count = await arun_society(society)
        print(f"\033[94mAnswer: {answer}\033[0m")
        print(f"\033[94mCompleted! Resume analysis has been saved to ./resume_analysis.md file\033[0m")

    finally:
        # Make sure to disconnect safely after all operations are completed.
        try:
            await mcp_toolkit.disconnect()
        except Exception:
            print("Disconnect failed")

if __name__ == "__main__":
    asyncio.run(main())
