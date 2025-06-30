#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import shutil
import datetime
import logging
from typing import Optional, Dict, Any, List

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from owl.utils import run_society
from camel.toolkits import FileWriteToolkit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_output_directories(base_dir: str = "outputs") -> Dict[str, Path]:
    """Setup output directory structure with cleanup of old files"""
    output_paths = {
        "base": Path(base_dir),
        "current": Path(base_dir) / datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "drafts": Path(base_dir) / "drafts",
        "final": Path(base_dir) / "final",
    }
    
    # Create directories
    for path in output_paths.values():
        path.mkdir(parents=True, exist_ok=True)
    
    # Cleanup old files (>7 days)
    cleanup_old_outputs(output_paths["base"])
    
    return output_paths

def cleanup_old_outputs(base_dir: Path, max_age_days: int = 7):
    """Clean up old output files and directories"""
    current_time = datetime.datetime.now()
    try:
        for item in base_dir.glob("*"):
            if item.is_file():
                file_time = datetime.datetime.fromtimestamp(item.stat().st_mtime)
                if (current_time - file_time).days > max_age_days:
                    item.unlink()
            elif item.is_dir() and not item.name in ["drafts", "final"]:
                dir_time = datetime.datetime.fromtimestamp(item.stat().st_mtime)
                if (current_time - dir_time).days > max_age_days:
                    shutil.rmtree(item)
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

def construct_society(
    task: str,
    output_dirs: Optional[Dict[str, Path]] = None,
    round_limit: int = 25
) -> Any:
    """Construct agent society with proper file handling"""
    if output_dirs is None:
        output_dirs = setup_output_directories()

    # Initialize file toolkit with current session directory
    file_toolkit = FileWriteToolkit(output_dir=str(output_dirs["current"]))
    
    # Enhanced task prompt that ensures file creation
    enhanced_task = f"""CRITICAL: Create output files for this task.

TASK: {task}

REQUIRED FILE CREATION STEPS:
1. Create a summary markdown file (.md) explaining your approach
2. Save the main output as a properly formatted file
3. For complex tasks, create both draft and final versions
4. Use descriptive filenames with timestamps
5. Verify file creation success

IMPORTANT: You MUST create output files before completing the task."""

    # Import required modules for society creation
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    from owl.utils import OwlRolePlaying
    import os
    
    # Check if Cloudflare credentials are available
    CF_API_TOKEN = os.getenv("CF_API_TOKEN")
    CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
    MODEL_TYPE = os.getenv("MODEL_TYPE", "@cf/meta/llama-3.1-8b-instruct")
    
    if not CF_API_TOKEN or not CF_ACCOUNT_ID:
        logger.error("CF_API_TOKEN and CF_ACCOUNT_ID must be set for Cloudflare Workers AI")
        raise ValueError("Cloudflare credentials not found. Please set CF_API_TOKEN and CF_ACCOUNT_ID environment variables.")
    
    # Create Cloudflare Workers AI models
    gateway_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1"
    
    # Create models for different components
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=MODEL_TYPE,
            api_key=CF_API_TOKEN,
            url=gateway_url,
            model_config_dict={"temperature": 0, "max_tokens": 4000},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=MODEL_TYPE,
            api_key=CF_API_TOKEN,
            url=gateway_url,
            model_config_dict={"temperature": 0, "max_tokens": 4000},
        ),
    }
    
    # Configure toolkits
    tools = [*file_toolkit.get_tools()]
    
    # Configure agent roles and parameters
    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}

    # Configure task parameters
    task_kwargs = {
        "task_prompt": enhanced_task,
        "with_task_specify": False,
    }

    # Configure agent society
    try:
        society = OwlRolePlaying(
            **task_kwargs,
            user_role_name="user",
            user_agent_kwargs=user_agent_kwargs,
            assistant_role_name="assistant",
            assistant_agent_kwargs=assistant_agent_kwargs,
        )
        return society
    except Exception as e:
        logger.error(f"Error constructing society: {str(e)}")
        raise

def main():
    """Main function to run the script"""
    if len(sys.argv) < 2:
        print("Usage: python run_cloudflare_workers.py 'Your task description here'")
        sys.exit(1)

    task = sys.argv[1]
    output_dirs = setup_output_directories()
    
    try:
        logger.info(f"Processing task: {task}")
        society = construct_society(task, output_dirs)
        
        # Run society simulation
        answer, chat_history, token_info = run_society(society)
        
        # Save outputs
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary
        summary_file = output_dirs["current"] / f"summary_{timestamp}.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"# Task Summary\n\nTask: {task}\n\n{answer}\n")
        
        # Save final result
        result_file = output_dirs["final"] / f"result_{timestamp}.txt"
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(str(answer))
        
        # Log completion
        logger.info(f"Task completed successfully")
        logger.info(f"Outputs saved to: {output_dirs['current']}")
        logger.info(f"Final result: {result_file}")
        
        # Display token usage
        if isinstance(token_info, dict):
            completion_tokens = token_info.get("completion_token_count", 0)
            prompt_tokens = token_info.get("prompt_token_count", 0)
            total_tokens = completion_tokens + prompt_tokens
            logger.info(
                f"Token usage: completion={completion_tokens}, "
                f"prompt={prompt_tokens}, total={total_tokens}"
            )
            
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
