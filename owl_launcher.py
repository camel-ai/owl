#!/usr/bin/env python3
"""
OWL Interactive Launcher
A user-friendly menu system to launch different OWL configurations
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def load_env_file(env_path: str = "goopleAPI.env"):
    """Load environment variables from .env file"""
    try:
        env_file = Path(env_path)
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
            print(f"✅ Loaded environment variables from {env_path}")
        else:
            print(f"⚠️  Environment file {env_path} not found")
    except Exception as e:
        print(f"⚠️  Error loading environment file: {e}")

def print_banner():
    """Print the OWL startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                     🦉 OWL LAUNCHER 🦉                      ║
    ║                Interactive AI Agent System                   ║
    ║              Choose Your Configuration Below                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_menu_header(title: str):
    """Print a formatted menu header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def get_user_choice(prompt: str, max_choice: int) -> int:
    """Get user choice with validation"""
    while True:
        try:
            choice = int(input(f"\n{prompt} (1-{max_choice}): "))
            if 1 <= choice <= max_choice:
                return choice
            else:
                print(f"❌ Please enter a number between 1 and {max_choice}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)

def select_owl_mode() -> Tuple[str, str, str]:
    """Select OWL mode and return script path, name, and description"""
    print_menu_header("SELECT OWL MODE")
    
    modes = [
        {
            "name": "🎭 Fiction Writing System",
            "description": "Professional fiction writing powered by Cloudflare Scout",
            "script": "community_usecase/owl_writing_team/run_iterative_owl_fiction.py",
            "example": "Write a sci-fi story about time travel"
        },
        {
            "name": "🔧 General Task System", 
            "description": "General task automation with Cloudflare Scout",
            "script": "examples/run_iterative_cloudflare_workers.py",
            "example": "Create a Python web scraper with documentation"
        },
        {
            "name": "📚 Original Fiction System",
            "description": "Original fiction system (no iteration)",
            "script": "community_usecase/owl_writing_team/run_real_owl_fiction.py",
            "example": "Create a fantasy adventure story"
        },
        {
            "name": "⚡ Original General System",
            "description": "Original general system (no iteration)", 
            "script": "examples/run_cloudflare_workers.py",
            "example": "Analyze data and create a report"
        },
        {
            "name": "🧠 Learning Assistant (OpenAI)",
            "description": "AI learning companion with research tools (requires OpenAI)",
            "script": "community_usecase/learning-assistant/run_gpt4o.py",
            "example": "Learn about machine learning fundamentals"
        },
        {
            "name": "🦉 Learning Assistant (Cloudflare)",
            "description": "AI learning companion powered by Cloudflare Workers AI",
            "script": "community_usecase/learning-assistant/run_cloudflare.py",
            "example": "Create a learning plan for neural networks"
        }
    ]
    
    for i, mode in enumerate(modes, 1):
        print(f"{i}. {mode['name']}")
        print(f"   📝 {mode['description']}")
        print(f"   💡 Example: {mode['example']}")
        print()
    
    choice = get_user_choice("Select OWL mode", len(modes))
    selected = modes[choice - 1]
    
    print(f"\n✅ Selected: {selected['name']}")
    return selected['script'], selected['name'], selected['description']

def show_system_info():
    """Show information about the Cloudflare Scout system"""
    print_menu_header("🦉 CLOUDFLARE SCOUT SYSTEM")
    
    print("🎯 This OWL system uses Cloudflare's Llama Scout model:")
    print("   🦉 Llama 4 Scout: Advanced language model for story generation")
    print("   🔍 Iterative Quality Assessment")
    print()
    print("✨ Benefits:")
    print("   • Professional-grade fiction writing")
    print("   • High-quality iterative refinement")
    print("   • Consistent story generation")
    print()
    print("📋 Requirements:")
    print("   • CF_API_TOKEN + CF_ACCOUNT_ID for Cloudflare")
    print()

def select_quality_settings() -> Tuple[float, int]:
    """Select quality threshold and max iterations"""
    print_menu_header("QUALITY SETTINGS")
    
    print("🎯 Quality Threshold Options:")
    quality_options = [
        {"name": "🥉 Standard (7.0/10)", "value": 7.0, "desc": "Good quality, faster completion"},
        {"name": "🥈 High (7.5/10)", "value": 7.5, "desc": "High quality, balanced approach"},
        {"name": "🥇 Professional (8.5/10)", "value": 8.5, "desc": "Professional grade, slower but excellent"},
        {"name": "💎 Exceptional (9.0/10)", "value": 9.0, "desc": "Exceptional quality, maximum refinement"},
        {"name": "🏆 Perfection (9.5/10)", "value": 9.5, "desc": "Near-perfect quality, very slow"}
    ]
    
    for i, option in enumerate(quality_options, 1):
        print(f"{i}. {option['name']}")
        print(f"   📊 {option['desc']}")
        print()
    
    quality_choice = get_user_choice("Select quality threshold", len(quality_options))
    quality_threshold = quality_options[quality_choice - 1]["value"]
    
    print(f"\n🔄 Max Iterations Options:")
    iteration_options = [
        {"name": "⚡ Quick (2 iterations)", "value": 2, "desc": "Fast results, basic improvement"},
        {"name": "🚀 Standard (3 iterations)", "value": 3, "desc": "Balanced speed and quality"},
        {"name": "🎯 Thorough (5 iterations)", "value": 5, "desc": "Comprehensive improvement"},
        {"name": "🔬 Deep (7 iterations)", "value": 7, "desc": "Extensive refinement"},
        {"name": "🏅 Maximum (10 iterations)", "value": 10, "desc": "Ultimate quality pursuit"}
    ]
    
    for i, option in enumerate(iteration_options, 1):
        print(f"{i}. {option['name']}")
        print(f"   ⏱️  {option['desc']}")
        print()
    
    iteration_choice = get_user_choice("Select max iterations", len(iteration_options))
    max_iterations = iteration_options[iteration_choice - 1]["value"]
    
    print(f"\n✅ Quality Settings:")
    print(f"   🎯 Threshold: {quality_threshold}/10")
    print(f"   🔄 Max Iterations: {max_iterations}")
    
    return quality_threshold, max_iterations

def get_task_input() -> str:
    """Get task description from user"""
    print_menu_header("TASK INPUT")
    
    print("📝 Task Input Options:")
    print("1. 💬 Type your task directly")
    print("2. 📄 Load from text file")
    print("3. 🎲 Use example task")
    print()
    
    choice = get_user_choice("Select input method", 3)
    
    if choice == 1:
        print("\n📝 Enter your task description:")
        print("   (Press Enter twice when finished)")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        
        task = "\n".join(lines).strip()
        if not task:
            print("❌ No task entered, using example task")
            return "Create a comprehensive analysis with detailed recommendations"
        return task
    
    elif choice == 2:
        file_path = input("\n📄 Enter path to text file: ").strip()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                task = f.read().strip()
            if not task:
                print("❌ File is empty, using example task")
                return "Create a comprehensive analysis with detailed recommendations"
            print(f"✅ Loaded task from {file_path}")
            return task
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            print("Using example task instead")
            return "Create a comprehensive analysis with detailed recommendations"
    
    else:  # choice == 3
        examples = [
            "Write a compelling short story about artificial intelligence gaining consciousness",
            "Create a Python web scraper with full documentation and error handling", 
            "Develop a comprehensive business plan for a sustainable energy startup",
            "Design a complete workout routine with nutrition guidelines",
            "Write a technical tutorial on machine learning for beginners"
        ]
        
        print("\n🎲 Example Tasks:")
        for i, example in enumerate(examples, 1):
            print(f"{i}. {example}")
        print()
        
        example_choice = get_user_choice("Select example task", len(examples))
        task = examples[example_choice - 1]
        print(f"\n✅ Selected: {task}")
        return task

def build_command(script_path: str, task: str, quality_threshold: float, max_iterations: int) -> List[str]:
    """Build the command to execute with quality settings"""
    project_root = Path(__file__).parent.absolute()
    full_script_path = project_root / script_path
    
    # Set environment variables for quality settings
    env_vars = {
        "MAX_ITERATIONS": str(max_iterations),
        "QUALITY_THRESHOLD": str(quality_threshold)
    }
    
    # Update environment
    for key, value in env_vars.items():
        os.environ[key] = value
    
    command = ["python", str(full_script_path), task]
    return command

def confirm_execution(script_name: str, script_path: str, task: str, quality_threshold: float, max_iterations: int) -> bool:
    """Confirm execution with user"""
    print_menu_header("EXECUTION CONFIRMATION")
    
    print(f"🎯 Configuration Summary:")
    print(f"   📜 Script: {script_name}")
    print(f"   📝 Task: {task[:100]}{'...' if len(task) > 100 else ''}")
    print(f"   🎯 Quality Threshold: {quality_threshold}/10")
    print(f"   🔄 Max Iterations: {max_iterations}")
    print()
    
    print("🚀 Execution Options:")
    print("1. ✅ Execute now")
    print("2. 📋 Show full command")
    print("3. ❌ Cancel and restart")
    print()
    
    choice = get_user_choice("Select option", 3)
    
    if choice == 1:
        return True
    elif choice == 2:
        command = build_command(script_path, task, quality_threshold, max_iterations)
        print(f"\n📋 Full command would be:")
        print(f"   {' '.join(command)}")
        print(f"\n   Environment variables:")
        print(f"   MAX_ITERATIONS={max_iterations}")
        print(f"   QUALITY_THRESHOLD={quality_threshold}")
        return confirm_execution(script_name, script_path, task, quality_threshold, max_iterations)
    else:
        return False

def execute_owl(script_path: str, task: str, quality_threshold: float, max_iterations: int):
    """Execute the selected OWL configuration with live progress updates"""
    print_menu_header("EXECUTING OWL")
    
    command = build_command(script_path, task, quality_threshold, max_iterations)
    
    print(f"🚀 Starting OWL execution...")
    print(f"   📊 Quality target: {quality_threshold}/10")
    print(f"   🔄 Max iterations: {max_iterations}")
    print(f"   ⏰ Started at: {os.popen('date').read().strip()}")
    print(f"\n{'='*60}")
    
    try:
        # Execute with direct output - no buffering or capturing
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output
        
        print("🔄 OWL is working - showing full output:")
        print(f"{'='*60}")
        sys.stdout.flush()
        
        # Run directly without capturing output for real-time display
        return_code = subprocess.run(command, env=env).returncode
        
        print(f"\n{'='*60}")
        if return_code == 0:
            print(f"✅ OWL execution completed successfully!")
            print(f"   📁 Check the outputs directory for results")
        else:
            print(f"❌ OWL execution failed with code: {return_code}")
            
        print(f"   ⏰ Finished at: {os.popen('date').read().strip()}")
        
    except KeyboardInterrupt:
        print(f"\n{'='*60}")
        print(f"⚠️  OWL execution interrupted by user")
        print(f"   📂 Partial results may be available in outputs directory")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ Unexpected error: {str(e)}")

def main():
    """Main launcher function"""
    try:
        # Load environment variables from .env file
        load_env_file()
        
        print_banner()
        
        while True:
            # Step 1: Select OWL mode
            script_path, script_name, description = select_owl_mode()
            
            # Step 2: Show system info for iterative scripts
            if "iterative" in script_path:
                show_system_info()
                quality_threshold, max_iterations = select_quality_settings()
            else:
                quality_threshold, max_iterations = 7.5, 3
                print(f"\n💡 Using default settings for non-iterative script")
            
            # Step 3: Get task input
            task = get_task_input()
            
            # Step 4: Confirm and execute
            if confirm_execution(script_name, script_path, task, quality_threshold, max_iterations):
                execute_owl(script_path, task, quality_threshold, max_iterations)
                break
            else:
                print("\n🔄 Restarting configuration...\n")
                continue
    
    except KeyboardInterrupt:
        print(f"\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Launcher error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
