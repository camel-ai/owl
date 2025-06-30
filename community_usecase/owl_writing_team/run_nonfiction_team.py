#!/usr/bin/env python3
"""
OWL Non-Fiction Writing Team
Specialized multi-agent system for research-heavy, authoritative writing
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


class OWLNonFictionTeam:
    """Specialized OWL team for non-fiction writing projects"""
    
    def __init__(self):
        self.setup_models()
        self.setup_tools()
        self.setup_output_directory()
        
    def setup_models(self):
        """Configure models for authoritative non-fiction"""
        self.cf_api_key = os.getenv("CF_API_TOKEN")
        self.cf_account_id = os.getenv("CF_ACCOUNT_ID")
        
        if not self.cf_api_key or not self.cf_account_id:
            raise ValueError("CF_API_TOKEN and CF_ACCOUNT_ID must be set")
            
        self.gateway_url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id}/ai/v1"
        self.model_type = os.getenv("NONFICTION_MODEL", "@cf/meta/llama-4-scout-17b-16e-instruct")
        
        # Non-fiction optimized parameters (lower temperature for accuracy)
        self.model_config = {
            "temperature": float(os.getenv("NONFICTION_TEMPERATURE", "0.3")),
            "max_tokens": int(os.getenv("MAX_TOKENS", "8000")),
            "stream": False
        }
        
        logger.info(f"Non-Fiction Team configured with model: {self.model_type}")
        
    def setup_tools(self):
        """Setup research-focused tools"""
        self.output_dir = "./outputs/nonfiction/"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.tools = [
            *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
            SearchToolkit().search_duckduckgo,
            SearchToolkit().search_wiki,
            *FileWriteToolkit(output_dir=self.output_dir).get_tools(),
        ]
        
    def setup_output_directory(self):
        """Setup non-fiction specific output structure"""
        directories = [
            self.output_dir,
            f"{self.output_dir}/research",
            f"{self.output_dir}/sources", 
            f"{self.output_dir}/arguments",
            f"{self.output_dir}/drafts",
            f"{self.output_dir}/final"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def create_model(self):
        """Create research-optimized model"""
        return ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=self.model_type,
            api_key=self.cf_api_key,
            url=self.gateway_url,
            model_config_dict=self.model_config,
        )
        
    def create_nonfiction_society(self, writing_prompt: str, content_type: str = "article"):
        """Create non-fiction specialized writing society"""
        
        enhanced_prompt = f"""
NON-FICTION WRITING PROJECT: {writing_prompt}

CONTENT TYPE: {content_type}

SPECIALIZED NON-FICTION WRITING TEAM:
You are part of a professional non-fiction writing team focused on accuracy, authority, and persuasive argumentation:

1. **Research & Analysis**: Exhaustive research, fact verification, expert sources
2. **Argument & Logic**: Thesis development, logical structure, evidence organization  
3. **Expert Voice**: Authority establishment, credibility, professional tone
4. **Evidence Integration**: Research synthesis, citation management, data presentation
5. **Fact & Citation Quality**: Accuracy verification, source credibility, attribution

CRITICAL NON-FICTION REQUIREMENTS:
- Absolute factual accuracy with multiple source verification
- Strong logical argumentation and evidence-based reasoning
- Authoritative voice that establishes credibility and expertise
- Perfect citation format and source attribution
- Balanced perspective acknowledging counterarguments
- Professional presentation suitable for expert review

MANDATORY FILE OUTPUTS:
- Comprehensive research documentation with source evaluation
- Logical argument structure and evidence mapping
- Expert-level content with proper citations
- Fact-checking reports and verification status
- Final authoritative manuscript ready for publication
- Source bibliography with credibility assessments

NON-FICTION QUALITY STANDARDS:
- 99%+ factual accuracy with full verification
- Bulletproof logical consistency throughout
- Expert-level authority and credibility
- Perfect citation format compliance
- Intellectual honesty and balanced perspective
- Publication-ready professional quality

Focus on creating authoritative content that experts in the field would respect and reference.
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
            user_role_name="Research Editor",
            user_agent_kwargs=user_agent_kwargs,
            assistant_role_name="Non-Fiction Research Team",
            assistant_agent_kwargs=assistant_agent_kwargs,
        )
        
        return society
    
    def run_nonfiction_project(self, prompt: str, content_type: str = "article", round_limit: int = 40):
        """Execute a complete non-fiction writing project"""
        logger.info(f"Starting non-fiction project: {prompt}")
        logger.info(f"Content type: {content_type}")
        
        try:
            society = self.create_nonfiction_society(prompt, content_type)
            answer, chat_history, token_count = run_society(society, round_limit=round_limit)
            
            # Save non-fiction project summary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_content = f"""# Non-Fiction Writing Project Summary

**Project:** {prompt}
**Type:** {content_type}
**Completed:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Research Rounds:** {len(chat_history)}
**Token Usage:** {token_count}

## Final Content
{answer}

## Research Process
The non-fiction team developed this content through {len(chat_history)} collaborative rounds,
emphasizing thorough research, fact verification, logical argumentation, and expert-level presentation.

All research materials and sources have been saved to the outputs/nonfiction/ directory.
"""
            
            summary_filename = f"nonfiction_project_{timestamp}.md"
            with open(f"{self.output_dir}/{summary_filename}", "w", encoding="utf-8") as f:
                f.write(summary_content)
                
            logger.info(f"Non-fiction project summary saved: {summary_filename}")
            return answer, chat_history, token_count
            
        except Exception as e:
            logger.error(f"Non-fiction project failed: {e}")
            raise


def main():
    """Main execution for non-fiction writing"""
    if len(sys.argv) < 2:
        print("Usage: python run_nonfiction_team.py <research_prompt> [content_type]")
        print("Example: python run_nonfiction_team.py 'The impact of artificial intelligence on employment markets' 'research_report'")
        sys.exit(1)
    
    prompt = sys.argv[1]
    content_type = sys.argv[2] if len(sys.argv) > 2 else "article"
    
    nonfiction_team = OWLNonFictionTeam()
    
    try:
        answer, history, tokens = nonfiction_team.run_nonfiction_project(prompt, content_type)
        
        print("\n" + "="*60)
        print("📊 OWL NON-FICTION TEAM - RESEARCH COMPLETE")
        print("="*60)
        print(f"✅ Content Created: {answer[:200]}...")
        print(f"📑 Content Type: {content_type}")
        print(f"🔬 Research Rounds: {len(history)}")
        print(f"🔢 Token Usage: {tokens}")
        print(f"📁 Files saved to: {nonfiction_team.output_dir}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to complete non-fiction project: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()