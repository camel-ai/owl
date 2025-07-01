#!/usr/bin/env python3
"""
Llama Maverick Runner
Executes tasks using the Llama-4-Maverick-17B model via Gradio client
"""

import sys
from gradio_client import Client

def run_llama(task: str, system_message: str = "You are a helpful AI assistant.") -> str:
    """
    Run task through Llama Maverick model
    """
    try:
        # Initialize Gradio client with the full Hugging Face Space URL
        space_url = "https://huggingface.co/spaces/justa502man/meta-llama-Llama-4-Maverick-17B-128E-Instruct"
        print(f"🔄 Connecting to Hugging Face Space: {space_url}")
        client = Client(space_url)
        
        # Run prediction with enhanced error handling
        try:
            print("📡 Sending request to model...")
            result = client.predict(
                task,  # Direct task input
                fn_index=0  # Use the first (default) function
            )
            print("✅ Response received")
            if not result:
                raise ValueError("Empty response from model")
        except Exception as api_error:
            print(f"🚨 API Error: {str(api_error)}")
            print("⚠️ Trying fallback configuration...")
            # Attempt fallback with minimal parameters
            result = client.predict(
                task,
                api_name="/chat"
            )
        
        return result
    except Exception as e:
        print(f"❌ Error running Llama model: {str(e)}")
        sys.exit(1)

def main():
    """Main execution function"""
    # Get task from command line arguments
    if len(sys.argv) < 2:
        print("❌ Please provide a task")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    print(f"\n🦙 Running task through Llama Maverick...")
    print(f"📝 Task: {task}")
    print(f"\n{'='*60}")
    
    # Run task through model
    result = run_llama(task)
    
    # Print result
    print(f"\n✨ Result:")
    print(f"{'='*60}")
    print(result)
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
