#!/usr/bin/env python3
"""
OWL Writing Team - Main Orchestrator
A multi-agent writing system using Cloudflare Workers AI
"""

import os
import sys
import pathlib
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = pathlib.Path(__file__).parent
sys.path.insert(0, str(project_root.parent.parent))

from camel.models import ModelFactory
from camel.toolkits import (
    CodeExecutionToolkit,
    SearchToolkit,
    FileWriteToolkit,
)
from camel.types import ModelPlatformType
from camel.societies import RolePlaying
from camel.logger import set_log_level

from owl.utils import run_society
from agents.writing_planner import WritingPlanner
from agents.research_agent import ResearchAgent
from agents.creative_agent import CreativeAgent
from agents.structure_agent import StructureAgent
from agents.content_agent import ContentAgent
from agents.quality_agent import QualityAgent

# Load environment variables
env_path = project_root / "config" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="INFO")

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OWLWritingTeam:
    """Main orchestrator for the OWL Writing Team"""
    
    def __init__(self):
        self.setup_models()
        self.setup_tools()
        self.setup_output_directory()
        
    def setup_models(self):
        """Configure Cloudflare Workers AI models"""
        self.cf_api_key = os.getenv("CF_API_TOKEN")
        self.cf_account_id = os.getenv("CF_ACCOUNT_ID")
        
        if not self.cf_api_key or not self.cf_account_id:
            raise ValueError(
                "CF_API_TOKEN and CF_ACCOUNT_ID must be set in environment variables"
            )
            
        self.gateway_url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id}/ai/v1"
        self.model_type = os.getenv("PRIMARY_MODEL", "@cf/meta/llama-4-scout-17b-16e-instruct")
        
        self.model_config = {
            "temperature": float(os.getenv("TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("MAX_TOKENS", "8000")),
            "stream": False
        }
        
        logger.info(f"Configured Cloudflare AI: {self.gateway_url}")
        logger.info(f"Using model: {self.model_type}")
        
    def setup_tools(self):
        """Setup writing-specific tools"""
        self.output_dir = "./outputs/"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.tools = [
            *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
            SearchToolkit().search_duckduckgo,
            SearchToolkit().search_wiki,
            *FileWriteToolkit(output_dir=self.output_dir).get_tools(),
        ]
        
        logger.info(f"Configured {len(self.tools)} tools with output to: {self.output_dir}")
        
    def setup_output_directory(self):
        """Ensure output directory exists with proper structure"""
        directories = [
            self.output_dir,
            f"{self.output_dir}/drafts",
            f"{self.output_dir}/research",
            f"{self.output_dir}/final"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def create_model(self):
        """Create a configured Cloudflare model instance"""
        return ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=self.model_type,
            api_key=self.cf_api_key,
            url=self.gateway_url,
            model_config_dict=self.model_config,
        )
        
    def create_writing_society(self, writing_prompt: str, project_type: str = "general"):
        """Create a writing-focused RolePlaying society"""
        
        # Enhanced prompt with writing-specific requirements
        enhanced_prompt = f"""
WRITING PROJECT: {writing_prompt}

PROJECT TYPE: {project_type}

CRITICAL WRITING TEAM REQUIREMENTS:
1. You are part of a professional writing team with specialized roles
2. Follow the multi-agent writing process: Research → Structure → Content → Quality
3. Create high-quality, publication-ready content
4. Save ALL work products using the write_to_file tool:
   - Research findings and sources
   - Structural outlines and plans
   - Draft content sections
   - Final polished manuscript
   - Quality review reports

MANDATORY FILE OUTPUTS:
- Use descriptive filenames with timestamps
- Save to outputs/ directory automatically
- Create both draft and final versions
- Include research documentation
- Provide quality assessment reports

QUALITY STANDARDS:
- Professional publication level
- Proper citations and fact-checking
- Consistent voice and style
- Target audience optimization
- 85%+ first-draft acceptance rate

Your role depends on your specialization. Work collaboratively to produce exceptional written content.
"""

        # Create models for user and assistant
        models = {
            "user": self.create_model(),
            "assistant": self.create_model(),
        }
        
        # Configure agents
        user_agent_kwargs = {"model": models["user"]}
        assistant_agent_kwargs = {"model": models["assistant"], "tools": self.tools}
        
        # Create the society
        society = RolePlaying(
            task_prompt=enhanced_prompt,
            with_task_specify=False,
            user_role_name="Writing Coordinator",
            user_agent_kwargs=user_agent_kwargs,
            assistant_role_name="Writing Team",
            assistant_agent_kwargs=assistant_agent_kwargs,
        )
        
        return society
    
    def run_writing_project(self, prompt: str, project_type: str = "general", round_limit: int = 30):
        """Execute a complete writing project"""
        logger.info(f"Starting writing project: {prompt}")
        logger.info(f"Project type: {project_type}")
        
        try:
            # Create the writing society
            society = self.create_writing_society(prompt, project_type)
            
            # Run the collaborative writing process
            answer, chat_history, token_count = run_society(
                society, 
                round_limit=round_limit
            )
            
            # Log results
            logger.info("Writing project completed successfully")
            logger.info(f"Total rounds: {len(chat_history)}")
            logger.info(f"Token usage: {token_count}")
            
            # Save project summary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_content = f"""# Writing Project Summary

**Project:** {prompt}
**Type:** {project_type}
**Completed:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Rounds:** {len(chat_history)}
**Token Count:** {token_count}

## Final Result
{answer}

## Process Overview
The writing team completed this project through {len(chat_history)} collaborative rounds,
utilizing specialized agents for research, structure, content creation, and quality assurance.

Files have been saved to the outputs/ directory with appropriate timestamps.
"""
            
            summary_filename = f"project_summary_{timestamp}.md"
            with open(f"{self.output_dir}/{summary_filename}", "w", encoding="utf-8") as f:
                f.write(summary_content)
                
            logger.info(f"Project summary saved: {summary_filename}")
            
            return answer, chat_history, token_count
            
        except Exception as e:
            logger.error(f"Writing project failed: {e}")
            raise


def main():
    """Main execution function"""
    if len(sys.argv) < 2:
        print("Usage: python run_writing_team.py <writing_prompt> [project_type]")
        print("Example: python run_writing_team.py 'Write a 2000-word article about AI ethics' 'article'")
        sys.exit(1)
    
    prompt = sys.argv[1]
    project_type = sys.argv[2] if len(sys.argv) > 2 else "general"
    
    # Initialize the writing team
    writing_team = OWLWritingTeam()
    
    # Run the writing project
    try:
        answer, history, tokens = writing_team.run_writing_project(prompt, project_type)
        
        print("\n" + "="*60)
        print("🦉 OWL WRITING TEAM - PROJECT COMPLETE")
        print("="*60)
        print(f"✅ Final Result: {answer[:200]}...")
        print(f"📊 Collaborative Rounds: {len(history)}")
        print(f"🔢 Token Usage: {tokens}")
        print(f"📁 Files saved to: {writing_team.output_dir}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to complete writing project: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()