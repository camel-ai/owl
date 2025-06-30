#!/usr/bin/env python3
"""
OWL Fiction Writing Team
Specialized multi-agent system for fiction writing projects
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

# Load environment variables
env_path = project_root / "config" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="INFO")
logger = logging.getLogger(__name__)


class OWLFictionTeam:
    """Specialized OWL team for fiction writing projects"""
    
    def __init__(self):
        self.setup_models()
        self.setup_tools()
        self.setup_output_directory()
        
    def setup_models(self):
        """Configure Cloudflare Workers AI models for fiction"""
        self.cf_api_key = os.getenv("CF_API_TOKEN")
        self.cf_account_id = os.getenv("CF_ACCOUNT_ID")
        
        if not self.cf_api_key or not self.cf_account_id:
            raise ValueError("CF_API_TOKEN and CF_ACCOUNT_ID must be set")
            
        self.gateway_url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id}/ai/v1"
        self.model_type = os.getenv("FICTION_MODEL", "@cf/meta/llama-4-scout-17b-16e-instruct")
        
        # Fiction-optimized parameters
        self.model_config = {
            "temperature": float(os.getenv("FICTION_TEMPERATURE", "0.8")),  # Higher creativity
            "max_tokens": int(os.getenv("MAX_TOKENS", "8000")),
            "stream": False
        }
        
        logger.info(f"Fiction Team configured with model: {self.model_type}")
        
    def setup_tools(self):
        """Setup fiction-specific tools"""
        self.output_dir = "./outputs/fiction/"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.tools = [
            *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
            SearchToolkit().search_duckduckgo,
            SearchToolkit().search_wiki,
            *FileWriteToolkit(output_dir=self.output_dir).get_tools(),
        ]
        
    def setup_output_directory(self):
        """Setup fiction-specific output structure"""
        directories = [
            self.output_dir,
            f"{self.output_dir}/characters",
            f"{self.output_dir}/worldbuilding", 
            f"{self.output_dir}/plots",
            f"{self.output_dir}/drafts",
            f"{self.output_dir}/final"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def create_model(self):
        """Create fiction-optimized model"""
        return ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=self.model_type,
            api_key=self.cf_api_key,
            url=self.gateway_url,
            model_config_dict=self.model_config,
        )
        
    def create_fiction_society(self, writing_prompt: str, fiction_type: str = "short_story"):
        """Create fiction-specialized writing society"""
        
        enhanced_prompt = f"""
FICTION WRITING PROJECT: {writing_prompt}

FICTION TYPE: {fiction_type}

SPECIALIZED FICTION WRITING TEAM:
You are part of a professional fiction writing team with specialized creative roles:

1. **World & Character Development**: Rich settings, compelling characters, backstories
2. **Plot & Structure**: Story arcs, pacing, scene structure, narrative flow  
3. **Prose & Voice**: Writing style, dialogue, description, voice consistency
4. **Continuity & Logic**: Plot consistency, character development, world rules
5. **Fiction Quality**: Emotional impact, genre compliance, reader engagement

CRITICAL FICTION REQUIREMENTS:
- Create compelling, emotionally resonant stories
- Develop rich characters with clear motivations and growth arcs
- Build immersive worlds with consistent internal logic
- Maintain engaging narrative flow and proper pacing
- Write beautiful, engaging prose appropriate to genre
- Ensure story satisfaction and emotional payoff

MANDATORY FILE OUTPUTS:
- Character profiles and development arcs
- World-building documents and setting details
- Plot outlines and scene breakdowns
- Draft manuscript sections
- Final polished fiction piece
- Continuity and style guide

FICTION QUALITY STANDARDS:
- Emotionally engaging and memorable characters
- Satisfying plot with proper setup and payoff
- Immersive world-building that enhances story
- Genre-appropriate style and conventions
- Professional prose quality ready for publication
- Strong narrative voice and consistent tone

Focus on creating fiction that readers will find emotionally satisfying and memorable.
"""

        models = {
            "user": self.create_model(),
            "assistant": self.create_model(),
        }
        
        user_agent_kwargs = {"model": models["user"]}
        assistant_agent_kwargs = {"model": models["assistant"], "tools": self.tools}
        
        society = RolePlaying(
            task_prompt=enhanced_prompt,
            with_task_specify=False,
            user_role_name="Fiction Editor",
            user_agent_kwargs=user_agent_kwargs,
            assistant_role_name="Fiction Writing Team",
            assistant_agent_kwargs=assistant_agent_kwargs,
        )
        
        return society
    
    def run_fiction_project(self, prompt: str, fiction_type: str = "short_story", round_limit: int = 35):
        """Execute a complete fiction writing project"""
        logger.info(f"Starting fiction project: {prompt}")
        logger.info(f"Fiction type: {fiction_type}")
        
        try:
            society = self.create_fiction_society(prompt, fiction_type)
            answer, chat_history, token_count = run_society(society, round_limit=round_limit)
            
            # Save fiction project summary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_content = f"""# Fiction Writing Project Summary

**Project:** {prompt}
**Type:** {fiction_type}
**Completed:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Collaborative Rounds:** {len(chat_history)}
**Token Usage:** {token_count}

## Final Story
{answer}

## Creative Process
The fiction writing team developed this story through {len(chat_history)} collaborative rounds,
focusing on character development, world-building, plot structure, and prose quality.

All creative assets have been saved to the outputs/fiction/ directory.
"""
            
            summary_filename = f"fiction_project_{timestamp}.md"
            with open(f"{self.output_dir}/{summary_filename}", "w", encoding="utf-8") as f:
                f.write(summary_content)
                
            logger.info(f"Fiction project summary saved: {summary_filename}")
            return answer, chat_history, token_count
            
        except Exception as e:
            logger.error(f"Fiction project failed: {e}")
            raise


def main():
    """Main execution for fiction writing"""
    if len(sys.argv) < 2:
        print("Usage: python run_fiction_team.py <story_prompt> [fiction_type]")
        print("Example: python run_fiction_team.py 'A time traveler discovers they cannot return home' 'short_story'")
        sys.exit(1)
    
    prompt = sys.argv[1]
    fiction_type = sys.argv[2] if len(sys.argv) > 2 else "short_story"
    
    fiction_team = OWLFictionTeam()
    
    try:
        answer, history, tokens = fiction_team.run_fiction_project(prompt, fiction_type)
        
        print("\n" + "="*60)
        print("📚 OWL FICTION TEAM - STORY COMPLETE")
        print("="*60)
        print(f"✅ Story Created: {answer[:200]}...")
        print(f"🎭 Fiction Type: {fiction_type}")
        print(f"📊 Creative Rounds: {len(history)}")
        print(f"🔢 Token Usage: {tokens}")
        print(f"📁 Files saved to: {fiction_team.output_dir}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to complete fiction project: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()