#main.py
import os
import logging
import time
from typing import Dict, Any, Callable, Optional
from pathlib import Path
import sys

# Add parent directory to path for OWL imports
sys.path.append('../')
from dotenv import load_dotenv
import numpy as np  # Explicitly import numpy to avoid 'numpy' errors
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.toolkits import (
    SearchToolkit, 
    BrowserToolkit, 
    CodeExecutionToolkit
)
from camel.societies import RolePlaying
from camel.configs import ChatGPTConfig
from owl.utils import run_society  # Official run_society with round_limit support

# Import prompt templates
from config.prompts import (
    get_system_prompt, 
    get_company_research_prompt, 
    get_question_generator_prompt,
    get_preparation_plan_prompt
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create the output directory for interview preparation materials
INTERVIEW_PREP_DIR = "./interview_prep"
os.makedirs(INTERVIEW_PREP_DIR, exist_ok=True)

def run_society_with_strict_limit(society, round_limit=5, progress_callback=None):
    """Wrapper around run_society to ensure round limit is strictly enforced
    
    This implementation hijacks the step method to force termination after a specific number of rounds.
    """
    # Track rounds manually
    round_count = 0
    
    # Save original step function
    original_step = society.step
    
    # Override the step method
    def limited_step(*args, **kwargs):
        nonlocal round_count
        round_count += 1
        
        # Report progress if callback is provided
        if progress_callback and callable(progress_callback):
            progress_callback(round_count, round_limit)
            
        # Force termination after reaching the round limit
        if round_count >= round_limit:
            logger.info(f"Reached round limit of {round_limit}, forcibly terminating.")
            # Force a TASK_DONE in the user response to trigger termination
            result = original_step(*args, **kwargs)
            if len(result) >= 2 and hasattr(result[1], 'msgs') and result[1].msgs and len(result[1].msgs) > 0:
                result[1].msgs[0].content += "\n\nTASK_DONE"
                result[1].terminated = True
            return result
        
        return original_step(*args, **kwargs)
    
    # Replace the step method
    society.step = limited_step
    
    try:
        # Run the conversation with the standard run_society function
        answer, chat_history, token_count = run_society(society, round_limit=round_limit)
        
        # Add a note about the conversation being truncated
        if len(chat_history) > 0 and "truncated_note" not in chat_history[-1]:
            chat_history[-1]["truncated_note"] = True
            if "assistant" in chat_history[-1]:
                chat_history[-1]["assistant"] += "\n\n[Note: This conversation was limited to maintain response quality.]"
        
        return answer, chat_history, token_count
    
    finally:
        # Restore the original step method
        society.step = original_step

def construct_interview_assistant(
    job_description: str, 
    company_name: str,
    detailed: bool = True,
    limited_searches: bool = True
) -> RolePlaying:
    """
    Construct a specialized interview preparation assistant using OWL.
    """
    # Select model based on environment variables
    if os.environ.get("OPENROUTER_API_KEY"):
        logger.info("Using OpenRouter with Gemini model")
        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            model_type="google/gemini-2.0-flash-001",
            url="https://openrouter.ai/api/v1",
            model_config_dict={
                "temperature": 0.6,
                "max_tokens": 4000,  # Reduced from 10000 to avoid exceeding limits
                # Do NOT use context_length - it's not a valid API parameter
            }
        )
    elif os.environ.get("OPENAI_API_KEY"):
        logger.info("Using OpenAI model (GPT-4)")
        config = ChatGPTConfig(
            temperature=0.3,
            max_tokens=4000
        )
        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=config.as_dict()
        )
    else:
        raise ValueError("Either OPENAI_API_KEY or OPENROUTER_API_KEY must be set")
    
    # Configure toolkits - Remove FileWriteToolkit as requested
    essential_tools = [
        SearchToolkit().search_duckduckgo,
        SearchToolkit().search_wiki,
        # Removed the FileWriteToolkit as requested
    ]
    
    if os.environ.get("GOOGLE_API_KEY") and os.environ.get("SEARCH_ENGINE_ID"):
        essential_tools.append(SearchToolkit().search_google)
    
    if detailed:
        tools = [
            *essential_tools,
            *BrowserToolkit(
                headless=True,
                web_agent_model=model,
                planning_agent_model=model,
            ).get_tools(),
            *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
        ]
        logger.info("Using full toolset for comprehensive results (detailed=True)")
    else:
        tools = essential_tools
        logger.info("Using essential toolset for faster results (detailed=False)")
    
    user_agent_kwargs = {"model": model}
    assistant_agent_kwargs = {"model": model, "tools": tools}
    
    # Build enhanced prompt asking for full, detailed output
    base_prompt = get_system_prompt()
    enhanced_prompt = f"""{base_prompt}
Task: Help me prepare for an interview at {company_name} for the position of {job_description}.
Requirements:
1. Provide a highly detailed, extremely comprehensive response (aim for at least 2000+ words).
2. Structure the output with clear sections, actionable insights, examples, and code where relevant.
3. Tailor the content specifically to {company_name} and the {job_description} role.
4. Do NOT truncate or summarize—provide the full explanation directly.
"""
    
    task_kwargs = {
        "task_prompt": enhanced_prompt,
        "with_task_specify": False,
    }
    
    society = RolePlaying(
        **task_kwargs,
        user_role_name="job_seeker",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="interview_coach",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )
    
    # Try to set memory parameters to reduce context size
    try:
        # Try to access the context creator if it exists
        if hasattr(society, '_context_creator') and hasattr(society._context_creator, 'max_tokens'):
            society._context_creator.max_tokens = 4000
        # Alternative approach through kwargs if available
        elif hasattr(society, '_context_creator_kwargs'):
            society._context_creator_kwargs = {"max_tokens": 4000}
    except AttributeError:
        logger.warning("Could not directly set memory parameters. Using default values.")
    
    return society

def research_company(
    company_name: str, 
    detailed: bool = True, 
    limited_searches: bool = True,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    start_time = time.time()
    logging.info(f"Beginning company research for {company_name}")
    base_prompt = get_company_research_prompt(company_name)
    enhanced_prompt = f"""{base_prompt}

Please provide the most detailed, in-depth report possible, with no summarization or truncation.
Your response must include extensive coverage, code samples (if relevant), and be at least 2000 words long.
"""
    society = construct_interview_assistant("", company_name, detailed=detailed, limited_searches=limited_searches)
    society.task_prompt = enhanced_prompt
    
    # Use our strict wrapper function to enforce limit at exactly 5 rounds
    answer, chat_history, token_count = run_society_with_strict_limit(
        society, 
        round_limit=5,
        progress_callback=progress_callback
    )
    
    duration = time.time() - start_time
    logging.info(f"Completed company research for {company_name} in {duration:.2f} seconds")
    
    # Find any files that may have been generated
    generated_files = [str(file) for file in Path(INTERVIEW_PREP_DIR).glob("*") if file.is_file()]
    
    return {
        "answer": answer,
        "chat_history": chat_history,
        "token_count": token_count,
        "generated_files": generated_files,
        "duration_seconds": duration
    }

def generate_interview_questions(
    job_role: str, 
    company_name: str, 
    detailed: bool = True, 
    limited_searches: bool = True,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    start_time = time.time()
    logging.info(f"Starting question generation for {job_role} at {company_name} (detailed={detailed})")
    
    try:
        # Ensure numpy is available to prevent 'numpy' errors
        import numpy as np
        
        base_prompt = get_question_generator_prompt(job_role, company_name)
        enhanced_prompt = f"""{base_prompt}

Please provide at least 50 highly specific questions with code examples, multiple solution approaches, 
and extremely thorough explanations. Aim for 3000+ words, with no truncation or summarization.
"""
        society = construct_interview_assistant(job_role, company_name, detailed=detailed, limited_searches=limited_searches)
        society.task_prompt = enhanced_prompt
        
        # Use our wrapper function to strictly enforce a limit of 5 rounds
        answer, chat_history, token_count = run_society_with_strict_limit(
            society, 
            round_limit=5,
            progress_callback=progress_callback
        )
        
        duration = time.time() - start_time
        logging.info(f"Completed question generation for {job_role} at {company_name} in {duration:.2f} seconds")
        
        # Find any files that were generated
        generated_files = [str(file) for file in Path(INTERVIEW_PREP_DIR).glob("*") if file.is_file()]
        
        return {
            "answer": answer,
            "chat_history": chat_history,
            "token_count": token_count,
            "generated_files": generated_files,
            "duration_seconds": duration
        }
    
    except Exception as e:
        logging.error(f"Error in question generation: {str(e)}", exc_info=True)
        raise

def create_interview_prep_plan(
    job_role: str, 
    company_name: str, 
    detailed: bool = True, 
    limited_searches: bool = True,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    start_time = time.time()
    logging.info(f"Starting preparation plan creation for {job_role} at {company_name} (detailed={detailed})")
    
    try:
        base_prompt = get_preparation_plan_prompt(job_role, company_name)
        enhanced_prompt = f"""{base_prompt}

Please provide a highly thorough, step-by-step preparation plan with multiple days of tasks, 
detailed technical reviews, code examples where applicable, and at least 2000 words total. 
No truncation or summaries—include the full content.
"""
        society = construct_interview_assistant(job_role, company_name, detailed=detailed, limited_searches=limited_searches)
        society.task_prompt = enhanced_prompt
        
        # Use our wrapper function with strict limit of 5 rounds
        answer, chat_history, token_count = run_society_with_strict_limit(
            society, 
            round_limit=5,
            progress_callback=progress_callback
        )
        
        duration = time.time() - start_time
        logging.info(f"Completed preparation plan creation in {duration:.2f} seconds")
        
        # Find any files that were generated
        generated_files = [str(file) for file in Path(INTERVIEW_PREP_DIR).glob("*") if file.is_file()]
        
        return {
            "answer": answer,
            "chat_history": chat_history,
            "token_count": token_count,
            "generated_files": generated_files,
            "duration_seconds": duration
        }
    
    except Exception as e:
        logging.error(f"Error in preparation plan creation: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    job_role = "Machine Learning Engineer"
    company_name = "Google"
    result = create_interview_prep_plan(job_role, company_name, detailed=True)
    print(f"Answer: {result['answer']}")
    print(f"Generated files: {result['generated_files']}")
    print(f"Execution time: {result['duration_seconds']:.2f} seconds")
    print(f"Conversation rounds: {len(result['chat_history'])}")