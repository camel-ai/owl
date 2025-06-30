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
from groq import Groq
import asyncio

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

# Groq configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "compound-beta")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "1024"))

def setup_owl_fiction_directories(base_dir: str = "outputs/fiction/real_owl") -> Dict[str, Path]:
    """Setup OWL fiction output directory structure"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    story_dir = Path(base_dir).resolve()
    story_title = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    output_paths = {
        "base": story_dir,
        "current": story_dir / story_title,
        "drafts": story_dir / story_title / "drafts",
        "final": story_dir / story_title / "final",
        "characters": story_dir / story_title / "characters",
        "scenes": story_dir / story_title / "scenes",
        "worldbuilding": story_dir / story_title / "worldbuilding",
        "plots": story_dir / story_title / "plots",
        "research": story_dir / story_title / "research"
    }
    
    for path in output_paths.values():
        path.mkdir(parents=True, exist_ok=True)
    
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

def generate_draft_with_groq(prompt: str) -> str:
    """Generate story draft using Groq"""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        content = []
        
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=GROQ_MAX_TOKENS,
            top_p=1,
            stream=True,
        )

        for chunk in completion:
            chunk_content = chunk.choices[0].delta.content
            if chunk_content:
                content.append(chunk_content)
                
        return "".join(content)
    except Exception as e:
        logger.error(f"Groq API error: {str(e)}")
        return f"Error: {str(e)}"

def generate_owl_story(task: str, output_dirs: Dict[str, Path]) -> str:
    """Generate story content using OWL's enhanced approach"""
    steps = [
        {
            "name": "research",
            "prompt": f"Research and gather background information for this story prompt: {task}\n\nProvide relevant context, themes, and potential story elements.",
            "file": ("research", "background_research.md"),
            "use_groq": False
        },
        {
            "name": "outline",
            "prompt": "Create a detailed story outline with act structure, plot points, and narrative arc.",
            "file": ("plots", "story_outline.md"),
            "use_groq": False
        },
        {
            "name": "characters",
            "prompt": "Develop in-depth character profiles including backstories, motivations, and relationships.",
            "file": ("characters", "character_profiles.md"),
            "use_groq": False
        },
        {
            "name": "worldbuilding",
            "prompt": "Create detailed worldbuilding elements, setting descriptions, and atmosphere.",
            "file": ("worldbuilding", "world_details.md"),
            "use_groq": False
        },
        {
            "name": "scenes",
            "prompt": "Write detailed scene breakdowns with emotional beats and character interactions.",
            "file": ("scenes", "scene_descriptions.md"),
            "use_groq": False
        },
        {
            "name": "draft",
            "prompt": "Write a compelling and engaging first draft incorporating all elements into a cohesive narrative.",
            "file": ("drafts", "first_draft.md"),
            "use_groq": True
        },
        {
            "name": "revision",
            "prompt": "Polish and refine the draft, focusing on pacing, dialogue, and emotional impact.",
            "file": ("drafts", "revised_draft.md"),
            "use_groq": True
        },
        {
            "name": "final",
            "prompt": "Create the final polished version with enhanced prose and storytelling.",
            "file": ("final", "final_story.md"),
            "use_groq": True
        }
    ]
    
    story_content = ""
    current_context = task
    
    for step in steps:
        logger.info(f"Generating {step['name']}...")
        
        full_prompt = f"""Previous context: {current_context}

Task: {step['prompt']}

Guidelines:
- Maintain consistency with previous elements
- Focus on emotional depth and character development
- Ensure natural flow and pacing
- Create vivid, engaging content

Generate the {step['name']} phase content:"""

        # Use Groq for drafting and final writing steps
        if step["use_groq"]:
            content = generate_draft_with_groq(full_prompt)
        else:
            content = generate_text(full_prompt)
            
        current_context = f"{current_context}\n\n{step['name']}: {content[:500]}..."
        
        dir_key, filename = step['file']
        write_to_file(content, filename, output_dirs[dir_key])
        
        if step['name'] == 'final':
            story_content = content
            
    return story_content

def main():
    """Main function to run OWL fiction writing"""
    if len(sys.argv) < 2:
        print("Usage: python run_real_owl_fiction.py 'Your story prompt here'")
        sys.exit(1)

    task = sys.argv[1]
    output_dirs = setup_owl_fiction_directories()
    
    try:
        logger.info(f"Processing fiction task with OWL: {task}")
        
        final_story = generate_owl_story(task, output_dirs)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        story_title = "_".join(task.lower().split()[:5])
        
        write_to_file(
            f"# OWL Fiction Project: {task}\n\n{final_story}\n",
            f"project_summary_{timestamp}.md",
            output_dirs["current"]
        )
        
        write_to_file(
            f"# {task}\n\n{final_story}",
            f"{story_title}_{timestamp}.md",
            output_dirs["final"]
        )
        
        write_to_file(
            str(final_story),
            f"{story_title}_{timestamp}.txt",
            output_dirs["final"]
        )
        
        logger.info(f"OWL story writing completed successfully")
        logger.info(f"Project files saved to: {output_dirs['current']}")
            
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
