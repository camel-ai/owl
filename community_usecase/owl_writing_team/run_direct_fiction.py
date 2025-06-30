#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import shutil
import datetime
import logging
from typing import Optional, Dict, Any, List
import json
import requests
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Cloudflare configuration
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
MODEL_TYPE = os.getenv("MODEL_TYPE", "@cf/meta/llama-4-scout-17b-16e-instruct")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.8"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "10000"))

def setup_fiction_directories(base_dir: str = "outputs/fiction/direct") -> Dict[str, Path]:
    """Setup fiction output directory structure"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    story_dir = Path(base_dir).resolve()
    
    output_paths = {
        "base": story_dir,
        "current": story_dir / timestamp,
        "drafts": story_dir / timestamp / "drafts",
        "final": story_dir / timestamp / "final",
        "characters": story_dir / timestamp / "characters",
        "scenes": story_dir / timestamp / "scenes",
        "worldbuilding": story_dir / timestamp / "worldbuilding",
        "plots": story_dir / timestamp / "plots"
    }
    
    # Create directories
    for path in output_paths.values():
        path.mkdir(parents=True, exist_ok=True)
    
    # Cleanup old files (>7 days)
    cleanup_old_outputs(story_dir)
    
    return output_paths

def cleanup_old_outputs(base_dir: Path, max_age_days: int = 7):
    """Clean up old output files and directories"""
    current_time = datetime.datetime.now()
    try:
        for item in base_dir.glob("*"):
            if item.is_dir():
                dir_time = datetime.datetime.fromtimestamp(item.stat().st_mtime)
                if (current_time - dir_time).days > max_age_days:
                    shutil.rmtree(item)
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

def write_to_file(content: str, filename: str, directory: Path) -> bool:
    """Write content to file safely"""
    try:
        filepath = directory / filename
        directory.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to {filepath}: {str(e)}")
        return False

def generate_text(prompt: str) -> str:
    """Generate text using Cloudflare Workers AI"""
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL_TYPE}"
    
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "prompt": prompt,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success", False):
            return result.get("result", {}).get("response", "")
        else:
            error_msg = str(result.get("errors", ["Unknown error"])[0])
            logger.error(f"API Error: {error_msg}")
            return f"Error: {error_msg}"
            
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return f"Error: {str(e)}"

def generate_story(task: str, output_dirs: Dict[str, Path]) -> str:
    """Generate story content using a structured approach"""
    steps = [
        {
            "name": "outline",
            "prompt": f"Create a detailed outline for a story based on this prompt: {task}\n\nInclude character descriptions, plot points, and key scenes.",
            "file": ("plots", "story_outline.md")
        },
        {
            "name": "characters",
            "prompt": "Based on the outline, develop detailed character profiles and relationships.",
            "file": ("characters", "character_profiles.md")
        },
        {
            "name": "scenes",
            "prompt": "Write detailed scene descriptions following the outline.",
            "file": ("scenes", "scene_descriptions.md")
        },
        {
            "name": "draft",
            "prompt": "Write the first draft of the story, incorporating all elements.",
            "file": ("drafts", "first_draft.md")
        },
        {
            "name": "final",
            "prompt": "Polish and refine the story into its final form, focusing on quality and flow.",
            "file": ("final", "final_story.md")
        }
    ]
    
    story_content = ""
    for step in steps:
        logger.info(f"Generating {step['name']}...")
        content = generate_text(step['prompt'])
        
        # Save step output
        dir_key, filename = step['file']
        write_to_file(content, filename, output_dirs[dir_key])
        
        if step['name'] == 'final':
            story_content = content
            
    return story_content

def main():
    """Main function to run fiction writing"""
    if len(sys.argv) < 2:
        print("Usage: python run_direct_fiction.py 'Your story prompt here'")
        sys.exit(1)

    task = sys.argv[1]
    output_dirs = setup_fiction_directories()
    
    try:
        logger.info(f"Processing fiction task: {task}")
        
        # Generate story content
        final_story = generate_story(task, output_dirs)
        
        # Save project summary with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        story_title = "_".join(task.lower().split()[:5])
        
        write_to_file(
            f"# Fiction Project: {task}\n\n{final_story}\n",
            f"project_summary_{timestamp}.md",
            output_dirs["current"]
        )
        
        # Save final story in multiple formats
        for ext in ['.md', '.txt']:
            write_to_file(
                final_story,
                f"{story_title}_{timestamp}{ext}",
                output_dirs["final"]
            )
        
        logger.info(f"Story writing completed successfully")
        logger.info(f"Project files saved to: {output_dirs['current']}")
            
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
