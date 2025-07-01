#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv
import requests
from gradio_client import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Model configuration
MODEL_URL = "https://justa502man-llama4-maverick-17b.hf.space"
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "512"))

def setup_directories():
    """Setup output directories"""
    output_dir = Path("outputs/final")
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
    """Generate text using Llama Maverick model"""
    try:
        print(f"🔄 Connecting to model at {MODEL_URL}")
        client = Client(MODEL_URL)
        
        try:
            result = client.predict(
                prompt,  # Direct task input
                fn_index=0  # Use the first (default) function
            )
        except Exception as api_error:
            print(f"🚨 API Error: {str(api_error)}")
            print("⚠️ Trying fallback configuration...")
            result = client.predict(
                prompt,
                api_name="/chat"
            )
        
        # Print for visibility
        print(result)
        return result
            
    except Exception as e:
        logger.error(f"Hugging Face API error: {str(e)}")
        return f"Error: {str(e)}"

def process_task(task: str) -> str:
    """Process the task and generate response"""
    print("📝 Preparing task...")
    full_prompt = f"""You are a helpful AI assistant. Please help with the following task:

{task}

Provide a clear, thorough, and well-organized response."""
    
    return generate_text(full_prompt)

def main():
    """Main function to process tasks"""
    if len(sys.argv) < 2:
        print("Usage: python run_huggingface.py 'Your task description here'")
        sys.exit(1)

    task = sys.argv[1]
    output_dir = setup_directories()
    
    try:
        print(f"🚀 Processing task with Llama Maverick")
        print(f"Task: {task}")
        print("\n💭 Generating response...\n")
        
        response = process_task(task)
        
        # Save output
        timestamp = Path(sys.argv[0]).stem
        filename = f"response_{timestamp}.md"
        write_to_file(f"# Task Response\n\n{response}", filename, output_dir)
        
        print(f"\n✅ Response saved to: {output_dir / filename}")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
