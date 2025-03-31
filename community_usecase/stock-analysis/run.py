# Stock Analysis Agent with AI Agents, using OWL 🦉
# This is a stock analysis system based on OWL multi-agent technology
# The system contains two core components:
# 1. Stock Analysis Assistant - Provides comprehensive stock investment advice and analysis
# 2. SEC Financial Data Analysis Assistant - Focuses on analyzing SEC files and financial statements
# The system uses the 🦉(OWL) framework to coordinate multiple AI agents to complete complex stock analysis tasks

from argparse import Namespace
from typing import Any, List, Optional, Dict, Callable
import time

import os
import logging
import json
import argparse

from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelPlatformType,ModelType
from colorama import Fore, Style

from camel.toolkits import (
    SearchToolkit,
    FileWriteToolkit
)
from camel.societies import RolePlaying
from camel.logger import set_log_level, get_logger
from agent.sec_agent import get_sec_summary_for_company_tool
from prompts import get_system_prompt
from owl.utils import run_society
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Create the log directory for debugging and logging purposes
LOG_DIR = "./log"
os.makedirs(LOG_DIR, exist_ok=True)

# Create the output directory for interview preparation materials
REPORT_DIR = "./output"
os.makedirs(REPORT_DIR, exist_ok=True)

set_log_level(level="INFO")
logger = get_logger(__name__)
file_handler = logging.FileHandler(LOG_DIR+"/stock_analysis.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

root_logger = logging.getLogger()
root_logger.addHandler(file_handler)


def run_society_with_strict_limit(society, round_limit=5, progress_callback=None) -> tuple[str, List[dict[Any, Any]], dict[Any, Any]]:
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


def construct_stock_analysis_society( company_name: str) -> RolePlaying:
    """Construct a society of agents for the stock analysis.

    Args:
        task (str): Analyze relevant stock information and output a report.

    Returns:
        RolePlaying: A configured society of agents for the stock analysis.
    """
    models = {
       "user": ModelFactory.create(
            model_platform=ModelPlatformType.DEEPSEEK,
            model_type=ModelType.DEEPSEEK_CHAT,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.DEEPSEEK,
            model_type=ModelType.DEEPSEEK_CHAT,
            model_config_dict={"temperature": 0},
        ),
    }

    tools = [
        *FileWriteToolkit(output_dir=REPORT_DIR).get_tools(),
        SearchToolkit().search_baidu,
        get_sec_summary_for_company_tool
        
    ]

    if os.environ.get("GOOGLE_API_KEY") and os.environ.get("SEARCH_ENGINE_ID"):
        tools.append(SearchToolkit().search_google)

    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}

     # Build enhanced prompt asking for full, detailed output
    base_prompt = get_system_prompt()
    enhanced_prompt = f"""{base_prompt}
Task: Generate a comprehensive investment analysis report for {company_name}.
Requirements:
1. Research and collect company information:
   - Use search tools to gather general company background, industry position, and recent news
   - Utilize SEC tools to obtain financial statements and regulatory filings
   - Analyze key financial metrics and performance indicators

2. Generate a detailed markdown report with the following sections:
   - Company Overview and Business Model
   - Industry Analysis and Market Position
   - Financial Analysis (last 3-5 years)
     * Revenue and Profit Trends
     * Balance Sheet Analysis
     * Cash Flow Analysis
     * Key Financial Ratios
   - Risk Assessment
   - Investment Recommendation

3. Report Format Requirements:
   - Write in professional markdown format
   - Include data tables and key metrics
   - Minimum 2000 words comprehensive analysis
   - You MUST use the write_to_file tool to save the report as '{company_name}_investment_analysis.md'
   - Confirm the file has been written successfully before completing the task
"""

    task_kwargs = {
        "task_prompt": enhanced_prompt,
        "with_task_specify": False,
    }

    society = RolePlaying(
        **task_kwargs,
        user_role_name="financial_analyst",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="investment_advisor",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

    return society

def save_chat_history(chat_history: List[dict[Any, Any]], company_name: str) -> None:
    """Analyze chat history and extract tool call information."""

    # 保存聊天历史记录到文件
    chat_history_file = os.path.join(LOG_DIR, f"{company_name}_chat_history.json")
    with open(chat_history_file, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)

    print(f"{Fore.GREEN}Records saved to {chat_history_file}{Style.RESET_ALL}")

def parse_arguments() -> Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Stock Analysis Agent')
    parser.add_argument('--company', type=str, default="Google", help='Company name to analyze')
    parser.add_argument('--use-agentops', action='store_true', help='Enable AgentOps tracking')
    parser.add_argument('--rounds', type=int, default=5, help='Maximum conversation rounds')
    return parser.parse_args()

def init_agentops(use_agentops) -> bool:
    """Initialize AgentOps tracking (if enabled)"""
    if not use_agentops:
        return False
        
    import agentops
    agentops_api_key = os.getenv("AGENTOPS_API_KEY")
    if agentops_api_key:
        agentops.init(agentops_api_key, default_tags=["Stock Analysis Agent using owl"])
        print(f"{Fore.GREEN}AgentOps tracking enabled{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.YELLOW}Warning: AGENTOPS_API_KEY not set, AgentOps tracking disabled{Style.RESET_ALL}")
        return False

def generate_stock_investment_report(
    company_name: str,
    round_limit: int = 5, 
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    start_time = time.time()
    logging.info(f"Starting stock investment report generation for {company_name})")

    society = construct_stock_analysis_society(company_name=company_name)
    
    # Use our wrapper function to strictly enforce the round limit
    answer, chat_history, token_count = run_society_with_strict_limit(
        society, 
        round_limit=round_limit,
        progress_callback=progress_callback
    )
    
    duration = time.time() - start_time
    logging.info(f"Completed stock investment report generation for {company_name} in {duration:.2f} seconds")
    
    # Find any files that were generated
    generated_files = [str(file) for file in Path(REPORT_DIR).glob("*") if file.is_file()]
    
    return {
        "answer": answer,
        "chat_history": chat_history,
        "token_count": token_count,
        "generated_files": generated_files,
        "duration_seconds": duration
    }

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize AgentOps (if needed)
    agentops_enabled = init_agentops(args.use_agentops)
    
    company_name = args.company
    max_rounds = args.rounds
    
    print(f"{Fore.CYAN}=> Generating stock investment report for {company_name}...{Style.RESET_ALL}")
    result = generate_stock_investment_report(company_name, round_limit=max_rounds)
    
    print(f"{Fore.CYAN}=> Stock investment report generation completed!{Style.RESET_ALL}")
    # Record tool usage history
    save_chat_history(chat_history=result['chat_history'], company_name=company_name)

    print(f"{Fore.YELLOW}Answer: {Style.RESET_ALL}{result['answer']}\n")
    print(f"{Fore.BLUE}Generated files: {Style.RESET_ALL}{result['generated_files']}")
    print(f"{Fore.MAGENTA}Token Count: {Style.RESET_ALL}{result['token_count']}")
    print(f"{Fore.GREEN}Execution time: {Style.RESET_ALL}{result['duration_seconds']:.2f} seconds")
