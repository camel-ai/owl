#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv
import requests
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Hugging Face configuration
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen3-235B-A22B")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.8"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "10000"))

def setup_directories():
    """Setup output directories"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"outputs/fiction/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

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
    """Generate text using Hugging Face Inference API"""
    if not HF_TOKEN:
        logger.error("HF_TOKEN environment variable not set.")
        return "Error: HF_TOKEN is not configured."
    try:
        endpoint_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": TEMPERATURE,
                "max_new_tokens": MAX_TOKENS,
                "return_full_text": False
            },
            "options": {
                "wait_for_model": True
            }
        }
        
        response = requests.post(endpoint_url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if isinstance(result, list) and result and "generated_text" in result[0]:
            content = result[0]["generated_text"]
        elif isinstance(result, dict) and "generated_text" in result:
            content = result["generated_text"]
        else:
            logger.warning(f"Unexpected API response format: {result}")
            content = str(result)
            
        print(content)
            
        return content.strip()
            
    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error occurred: {http_err}"
        try:
            error_details = response.json()
            error_message += f" - {error_details}"
            logger.error(f"API Response Error: {error_details}")
        except ValueError:
            error_message += f" - Response: {response.text}"
        logger.error(error_message)
        return f"Error: {error_message}"
    except Exception as e:
        logger.error(f"Hugging Face API error: {str(e)}")
        return f"Error: {str(e)}"

def write_story(prompt: str) -> str:
    """Generate a story based on the prompt"""
    system_prompt = """You are a creative fiction writer focused on crafting engaging and well-structured stories.
Your writing should be imaginative, coherent, and emotionally resonant.
Create a complete story that includes:
- An engaging opening hook
- Well-developed characters
- Clear plot progression
- Descriptive settings
- Satisfying conclusion

Write the story now:"""
    
    full_prompt = f"{system_prompt}\n\nStory Prompt: {prompt}"
    return generate_text(full_prompt)

def main():
    """Main function to generate stories"""
    if len(sys.argv) < 2:
        print("Usage: python run_huggingface_fiction.py 'Your story prompt here'")
        sys.exit(1)

    prompt = sys.argv[1]
    output_dir = setup_directories()
    
    try:
        print(f"📝 Generating story with Hugging Face Chat ({HF_MODEL})")
        print(f"Prompt: {prompt}")
        print("\n💭 Writing story...\n")
        
        story = write_story(prompt)
        
        # Generate filename from prompt
        safe_name = "_".join(prompt.lower().split()[:5])
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.md"
        
        # Save story
        write_to_file(f"# {prompt}\n\n{story}", filename, output_dir)
        
        # Also save as plain text
        write_to_file(str(story), filename.replace(".md", ".txt"), output_dir)
        
        print(f"\n✅ Story saved to: {output_dir / filename}")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
