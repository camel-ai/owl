#!/usr/bin/env python3
import os
import sys
import json
import re
from pathlib import Path
import shutil
import datetime
import logging
import time
from typing import Optional, Dict, Any, List, Tuple
import requests

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from owl.utils import run_society
from camel.toolkits import FileWriteToolkit
from camel.societies import RolePlaying
from camel.models import ModelFactory
from camel.types import ModelPlatformType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Iteration configuration - Raised for higher quality standards
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "8.5"))

# Multi-model hybrid configuration - Use both platforms simultaneously
USE_HYBRID_MODELS = os.getenv("USE_HYBRID_MODELS", "true").lower() == "true"

# Cloudflare configuration
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_USER_MODEL = os.getenv("CF_USER_MODEL", "@cf/meta/llama-4-scout-17b-16e-instruct")
CF_ASSISTANT_MODEL = os.getenv("CF_ASSISTANT_MODEL", "@cf/meta/llama-4-scout-17b-16e-instruct")
CF_QUALITY_MODEL = os.getenv("CF_QUALITY_MODEL", "@cf/meta/llama-4-scout-17b-16e-instruct")

# Google Gemini configuration  

# Role assignments for hybrid mode
# User Agent: Gemini Pro (excellent for task understanding and feedback)
# Assistant Agent: Llama 4 Scout (fast execution with file tools)
# Quality Assessment: Both models for comprehensive evaluation

def setup_output_directories(base_dir: str = "outputs/iterative_owl") -> Dict[str, Path]:
    """Setup output directory structure with iteration tracking"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_paths = {
        "base": Path(base_dir),
        "current": Path(base_dir) / timestamp,
        "drafts": Path(base_dir) / timestamp / "drafts",
        "final": Path(base_dir) / timestamp / "final",
        "iterations": Path(base_dir) / timestamp / "iterations",
        "feedback": Path(base_dir) / timestamp / "feedback",
        "chat_history": Path(base_dir) / timestamp / "chat_history",
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
            elif item.is_dir() and not item.name in ["drafts", "final", "iterations", "feedback"]:
                dir_time = datetime.datetime.fromtimestamp(item.stat().st_mtime)
                if (current_time - dir_time).days > max_age_days:
                    shutil.rmtree(item)
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

def assess_output_quality(output: str, task: str, criteria: Dict[str, str]) -> Tuple[float, Dict[str, float], str]:
    """Assess the quality of OWL society output using AI evaluation"""
    
    # In hybrid mode, use both models for quality assessment and average the results
    if USE_HYBRID_MODELS and GOOGLE_API_KEY and CF_API_TOKEN and CF_ACCOUNT_ID:
        return assess_quality_hybrid(output, task, criteria)
    elif GOOGLE_API_KEY:
        return assess_quality_with_gemini(output, task, criteria)
    elif CF_API_TOKEN and CF_ACCOUNT_ID:
        return assess_quality_with_cloudflare(output, task, criteria)
    else:
        logger.warning("No AI credentials available, using basic quality assessment")
        return 6.0, {}, "Basic assessment: Output appears complete"

def assess_quality_hybrid(output: str, task: str, criteria: Dict[str, str]) -> Tuple[float, Dict[str, float], str]:
    """Assess quality using both Gemini and Cloudflare models, then combine results"""
    try:
        # Get assessments from both models
        gemini_score, gemini_dims, gemini_feedback = assess_quality_with_gemini(output, task, criteria)
        cf_score, cf_dims, cf_feedback = assess_quality_with_cloudflare(output, task, criteria)
        
        # Combine scores - weighted average (Gemini 60%, Cloudflare 40%)
        combined_score = (gemini_score * 0.6) + (cf_score * 0.4)
        
        # Combine dimension scores
        combined_dims = {}
        all_dims = set(gemini_dims.keys()) | set(cf_dims.keys())
        for dim in all_dims:
            g_score = gemini_dims.get(dim, gemini_score)
            c_score = cf_dims.get(dim, cf_score)
            combined_dims[dim] = (g_score * 0.6) + (c_score * 0.4)
        
        # Combine feedback
        combined_feedback = f"🔍 HYBRID QUALITY ASSESSMENT:\n\n" \
                           f"💎 GEMINI ANALYSIS (Score: {gemini_score:.1f}/10):\n{gemini_feedback}\n\n" \
                           f"🦉 LLAMA 4 ANALYSIS (Score: {cf_score:.1f}/10):\n{cf_feedback}\n\n" \
                           f"🎯 COMBINED ASSESSMENT (Score: {combined_score:.1f}/10):\n" \
                           f"Both models provide complementary perspectives. Focus on areas where both models identified improvements."
        
        logger.info(f"Hybrid quality assessment: Gemini {gemini_score:.1f}, Cloudflare {cf_score:.1f}, Combined {combined_score:.1f}")
        return combined_score, combined_dims, combined_feedback
        
    except Exception as e:
        logger.error(f"Error in hybrid quality assessment: {e}")
        # Fallback to single model assessment
        if GOOGLE_API_KEY:
            return assess_quality_with_gemini(output, task, criteria)
        else:
            return assess_quality_with_cloudflare(output, task, criteria)

def assess_quality_with_gemini(output: str, task: str, criteria: Dict[str, str]) -> Tuple[float, Dict[str, float], str]:
    """Assess quality using Google Gemini"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        
        model = genai.GenerativeModel(GEMINI_QUALITY_MODEL)
        
        quality_prompt = f"""
        Evaluate this OWL agent society output for the given task:
        
        TASK: {task}
        
        OUTPUT TO EVALUATE:
        {output[:5000]}...
        
        EVALUATION CRITERIA:
        {json.dumps(criteria, indent=2)}
        
        Provide scores (1-10) and feedback in this JSON format:
        {{
            "overall_score": 0.0,
            "dimension_scores": {{
                "criterion1": 0.0,
                "criterion2": 0.0
            }},
            "feedback": "Detailed feedback on strengths and areas for improvement",
            "improvement_suggestions": [
                "Specific suggestion 1",
                "Specific suggestion 2"
            ]
        }}
        """
        
        response = model.generate_content(quality_prompt)
        response_text = response.text
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            score_data = json.loads(json_match.group())
            overall_score = score_data.get("overall_score", 5.0)
            dimension_scores = score_data.get("dimension_scores", {})
            feedback = score_data.get("feedback", "") + "\n\nSuggestions:\n" + "\n".join(score_data.get("improvement_suggestions", []))
            return overall_score, dimension_scores, feedback
        
        return 6.0, {}, "Could not parse Gemini quality assessment"
        
    except Exception as e:
        logger.error(f"Error assessing quality with Gemini: {e}")
        return 5.0, {}, f"Error during Gemini quality assessment: {str(e)}"

def assess_quality_with_cloudflare(output: str, task: str, criteria: Dict[str, str]) -> Tuple[float, Dict[str, float], str]:
    """Assess quality using Cloudflare Workers AI"""
    
    quality_prompt = f"""
    Evaluate this OWL agent society output for the given task:
    
    TASK: {task}
    
    OUTPUT TO EVALUATE:
    {output[:3000]}...
    
    EVALUATION CRITERIA:
    {json.dumps(criteria, indent=2)}
    
    Provide scores (1-10) and feedback in this JSON format:
    {{
        "overall_score": 0.0,
        "dimension_scores": {{
            "criterion1": 0.0,
            "criterion2": 0.0
        }},
        "feedback": "Detailed feedback on strengths and areas for improvement",
        "improvement_suggestions": [
            "Specific suggestion 1",
            "Specific suggestion 2"
        ]
    }}
    """
    
    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CF_QUALITY_MODEL}"
        headers = {
            "Authorization": f"Bearer {CF_API_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "prompt": quality_prompt,
            "temperature": 0.3,
            "max_tokens": 8000
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success", False):
            response_text = result.get("result", {}).get("response", "")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                score_data = json.loads(json_match.group())
                overall_score = score_data.get("overall_score", 5.0)
                dimension_scores = score_data.get("dimension_scores", {})
                feedback = score_data.get("feedback", "") + "\n\nSuggestions:\n" + "\n".join(score_data.get("improvement_suggestions", []))
                return overall_score, dimension_scores, feedback
        
        return 5.0, {}, "Could not parse quality assessment"
        
    except Exception as e:
        logger.error(f"Error assessing quality: {e}")
        return 5.0, {}, f"Error during quality assessment: {str(e)}"

def generate_improvement_prompt(task: str, previous_output: str, feedback: str, iteration: int) -> str:
    """Generate improvement prompt based on feedback from previous iteration"""
    return f"""
    ITERATION {iteration} IMPROVEMENT TASK:
    
    Original task: {task}
    
    Previous output from OWL society:
    {previous_output}
    
    Quality feedback and areas for improvement:
    {feedback}
    
    INSTRUCTIONS FOR IMPROVEMENT:
    1. Address all specific feedback points from the quality assessment
    2. Enhance weak areas while maintaining strengths
    3. Improve overall task completion quality
    4. Ensure better agent coordination and output coherence
    5. Focus on the most critical improvements first
    
    ENHANCED TASK: {task}
    
    IMPROVEMENT REQUIREMENTS:
    - Build upon the previous attempt's strengths
    - Specifically address the feedback concerns
    - Produce a higher quality, more complete solution
    - Demonstrate better reasoning and problem-solving
    
    CRITICAL: Create output files that show clear improvement over the previous iteration.
    """

def construct_iterative_society(
    task: str,
    output_dirs: Dict[str, Path],
    round_limit: int = 25,
    previous_feedback: Optional[str] = None,
    iteration: int = 1
) -> RolePlaying:
    """Construct agent society with iterative improvement capabilities"""
    
    # Initialize file toolkit with current session directory
    file_toolkit = FileWriteToolkit(output_dir=str(output_dirs["current"]))
    
    # Enhanced task prompt with iteration awareness
    if iteration == 1:
        enhanced_task = f"""CRITICAL: Create high-quality output files for this task.

TASK: {task}

REQUIRED OUTPUT CREATION:
1. Create a comprehensive summary markdown file (.md) with your approach and findings
2. Save the main deliverable as a properly formatted file
3. For complex tasks, create both draft and final versions
4. Use descriptive filenames with timestamps
5. Include detailed reasoning and methodology
6. Verify all file creation success

QUALITY STANDARDS:
- Professional-grade output quality
- Clear, well-structured content
- Complete task fulfillment
- Proper documentation

IMPORTANT: You MUST create output files that demonstrate thorough task completion."""
    else:
        enhanced_task = generate_improvement_prompt(task, "", previous_feedback or "", iteration)
    
    # Create hybrid multi-model system using both platforms optimally
    user_model = None
    assistant_model = None
    
    if USE_HYBRID_MODELS and GOOGLE_API_KEY and CF_API_TOKEN and CF_ACCOUNT_ID:
        # HYBRID MODE: Use best model for each role
        # User Agent: Gemini Pro (excellent reasoning and task understanding)
        user_model = ModelFactory.create(
            model_platform=ModelPlatformType.GEMINI,
            model_type=GEMINI_USER_MODEL,
            api_key=GOOGLE_API_KEY,
            model_config_dict={"temperature": 0.4, "max_tokens": 8192},
        )
        
        # Assistant Agent: Llama 4 Scout (fast execution with tools, large context)
        assistant_model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=CF_ASSISTANT_MODEL,
            api_key=CF_API_TOKEN,
            url=f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1",
            model_config_dict={"temperature": 0.7, "max_tokens": 32000},
        )
        
        logger.info(f"🔥 HYBRID MODE: Gemini User ({GEMINI_USER_MODEL}) + Llama Assistant ({CF_ASSISTANT_MODEL})")
        
    elif GOOGLE_API_KEY:
        # Gemini-only mode
        user_model = ModelFactory.create(
            model_platform=ModelPlatformType.GEMINI,
            model_type=GEMINI_USER_MODEL,
            api_key=GOOGLE_API_KEY,
            model_config_dict={"temperature": 0.5, "max_tokens": 8192},
        )
        
        assistant_model = ModelFactory.create(
            model_platform=ModelPlatformType.GEMINI,
            model_type=GEMINI_ASSISTANT_MODEL,
            api_key=GOOGLE_API_KEY,
            model_config_dict={"temperature": 0.7, "max_tokens": 8192},
        )
        
        logger.info(f"💎 GEMINI MODE: {GEMINI_USER_MODEL}, {GEMINI_ASSISTANT_MODEL}")
        
    elif CF_API_TOKEN and CF_ACCOUNT_ID:
        # Cloudflare-only mode
        user_model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=CF_USER_MODEL,
            api_key=CF_API_TOKEN,
            url=f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1",
            model_config_dict={"temperature": 0.5, "max_tokens": 32000},
        )
        
        assistant_model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=CF_ASSISTANT_MODEL,
            api_key=CF_API_TOKEN,
            url=f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1",
            model_config_dict={"temperature": 0.7, "max_tokens": 32000},
        )
        
        logger.info(f"🦉 CLOUDFLARE MODE: {CF_USER_MODEL}, {CF_ASSISTANT_MODEL}")
    else:
        # No valid credentials available
        logger.error("No valid AI credentials found. Please set one of:")
        logger.error("- GOOGLE_API_KEY for Gemini")
        logger.error("- CF_API_TOKEN and CF_ACCOUNT_ID for Cloudflare")
        logger.error("- Both for hybrid mode (recommended)")
        raise ValueError("Missing AI model credentials")
    
    # Configure agent kwargs with role-specific models
    user_agent_kwargs = {"model": user_model} if user_model else {}
    assistant_agent_kwargs = {
        "model": assistant_model,
        "tools": [*file_toolkit.get_tools()],
    } if assistant_model else {"tools": [*file_toolkit.get_tools()]}
    
    # Configure task kwargs
    task_kwargs = {
        "task_prompt": enhanced_task,
        "with_task_specify": False,
    }
    
    # Configure agent society with tools
    try:
        society = RolePlaying(
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

def run_iterative_society(
    task: str,
    output_dirs: Dict[str, Path],
    round_limit: int = 25,
    max_iterations: int = MAX_ITERATIONS
) -> Tuple[str, List[dict], dict, List[dict]]:
    """Run OWL society with iterative improvement until quality threshold is met"""
    
    # Define enhanced quality criteria for general tasks - Higher standards
    quality_criteria = {
        "completeness": "Complete task fulfillment with all requirements addressed comprehensively",
        "accuracy": "Factual accuracy, correctness, and error-free implementation",
        "clarity": "Exceptional clarity, organization, and professional communication",
        "usefulness": "High practical value, real-world applicability, and actionable insights",
        "methodology": "Sound reasoning, best practices, and systematic approach",
        "innovation": "Creative solutions, efficiency improvements, and thoughtful enhancements",
        "documentation": "Comprehensive documentation, clear explanations, and proper formatting",
        "scalability": "Robust design that can handle edge cases and future requirements"
    }
    
    iteration_history = []
    best_output = ""
    best_score = 0.0
    final_chat_history = []
    final_token_info = {}
    
    for iteration in range(1, max_iterations + 1):
        logger.info(f"Starting iteration {iteration}/{max_iterations}")
        
        # Get previous feedback for improvement
        previous_feedback = None
        if iteration > 1 and iteration_history:
            previous_feedback = iteration_history[-1]["feedback"]
        
        # Construct society for this iteration
        society = construct_iterative_society(
            task, 
            output_dirs, 
            round_limit, 
            previous_feedback, 
            iteration
        )
        
        # Run society
        try:
            answer, chat_history, token_info = run_society(society, round_limit)
            
            # Assess output quality
            overall_score, dimension_scores, feedback = assess_output_quality(
                str(answer), task, quality_criteria
            )
            
            # Record iteration data
            iteration_data = {
                "iteration": iteration,
                "output": str(answer),
                "overall_score": overall_score,
                "dimension_scores": dimension_scores,
                "feedback": feedback,
                "chat_history": chat_history,
                "token_info": token_info,
                "timestamp": datetime.datetime.now().isoformat()
            }
            iteration_history.append(iteration_data)
            
            # Save iteration files
            iteration_file = output_dirs["iterations"] / f"iteration_{iteration}.json"
            with open(iteration_file, "w", encoding="utf-8") as f:
                json.dump(iteration_data, f, indent=2, default=str)
            
            output_file = output_dirs["iterations"] / f"output_{iteration}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# Iteration {iteration} Output\n\n{answer}\n")
            
            chat_file = output_dirs["chat_history"] / f"chat_{iteration}.json"
            with open(chat_file, "w", encoding="utf-8") as f:
                json.dump(chat_history, f, indent=2, default=str)
            
            logger.info(f"Iteration {iteration} completed - Score: {overall_score:.1f}/10")
            
            # Track best output
            if overall_score > best_score:
                best_output = str(answer)
                best_score = overall_score
                final_chat_history = chat_history
                final_token_info = token_info
            
            # Check if quality threshold is met
            if overall_score >= QUALITY_THRESHOLD:
                logger.info(f"Quality threshold ({QUALITY_THRESHOLD}) reached in {iteration} iterations")
                break
                
        except Exception as e:
            logger.error(f"Error in iteration {iteration}: {str(e)}")
            iteration_data = {
                "iteration": iteration,
                "output": f"Error: {str(e)}",
                "overall_score": 0.0,
                "dimension_scores": {},
                "feedback": f"Iteration failed: {str(e)}",
                "chat_history": [],
                "token_info": {},
                "timestamp": datetime.datetime.now().isoformat()
            }
            iteration_history.append(iteration_data)

        # Add a delay to avoid hitting API rate limits, especially on free tiers.
        # The Gemini API free tier has a low requests-per-minute limit.
        # The error log suggests a retry delay of 20-30 seconds.
        if iteration < max_iterations:
            delay = 30
            logger.info(
                f"Waiting for {delay} seconds before the next iteration to "
                f"respect API rate limits..."
            )
            time.sleep(delay)
    
    # Generate iteration summary
    summary = {
        "task": task,
        "total_iterations": len(iteration_history),
        "best_score": best_score,
        "final_score": iteration_history[-1]["overall_score"] if iteration_history else 0.0,
        "improvement": (iteration_history[-1]["overall_score"] - iteration_history[0]["overall_score"]) if len(iteration_history) > 1 else 0.0,
        "quality_threshold": QUALITY_THRESHOLD,
        "threshold_met": best_score >= QUALITY_THRESHOLD,
        "iteration_scores": [h["overall_score"] for h in iteration_history],
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Save summary
    summary_file = output_dirs["feedback"] / "iteration_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Iterative process completed. Best score: {best_score:.1f}/10")
    
    return best_output, final_chat_history, final_token_info, iteration_history

def main():
    """Main function to run iterative OWL society"""
    if len(sys.argv) < 2:
        print("Usage: python run_iterative_cloudflare_workers.py 'Your task description here'")
        sys.exit(1)

    task = sys.argv[1]
    output_dirs = setup_output_directories()
    
    try:
        logger.info(f"Processing task with Iterative OWL: {task}")
        logger.info(f"Max iterations: {MAX_ITERATIONS}")
        logger.info(f"Quality threshold: {QUALITY_THRESHOLD}/10")
        
        # Run iterative society
        best_output, chat_history, token_info, iteration_history = run_iterative_society(
            task, output_dirs
        )
        
        # Save final outputs
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save best result summary
        summary_file = output_dirs["current"] / f"final_summary_{timestamp}.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"# Iterative OWL Task Completion\n\n")
            f.write(f"**Task:** {task}\n\n")
            f.write(f"**Iterations:** {len(iteration_history)}\n\n")
            f.write(f"**Best Score:** {max(h['overall_score'] for h in iteration_history):.1f}/10\n\n")
            f.write(f"**Final Output:**\n\n{best_output}\n")
        
        # Save best result to final directory
        result_file = output_dirs["final"] / f"best_result_{timestamp}.txt"
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(str(best_output))
        
        # Save complete iteration history
        history_file = output_dirs["current"] / f"complete_history_{timestamp}.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(iteration_history, f, indent=2, default=str)
        
        # Log completion
        logger.info(f"Iterative OWL task completed successfully")
        logger.info(f"Best output saved to: {result_file}")
        logger.info(f"Iteration history saved to: {output_dirs['iterations']}")
        logger.info(f"Quality feedback saved to: {output_dirs['feedback']}")
        
        # Display final statistics
        best_score = max(h['overall_score'] for h in iteration_history)
        improvement = iteration_history[-1]['overall_score'] - iteration_history[0]['overall_score'] if len(iteration_history) > 1 else 0.0
        
        logger.info(f"Final Statistics:")
        logger.info(f"  - Total iterations: {len(iteration_history)}")
        logger.info(f"  - Best score: {best_score:.1f}/10")
        logger.info(f"  - Quality improvement: {improvement:+.1f}")
        logger.info(f"  - Threshold met: {'Yes' if best_score >= QUALITY_THRESHOLD else 'No'}")
        
        # Display token usage
        if isinstance(token_info, dict):
            completion_tokens = token_info.get("completion_token_count", 0)
            prompt_tokens = token_info.get("prompt_token_count", 0)
            total_tokens = completion_tokens + prompt_tokens
            logger.info(
                f"Token usage (best iteration): completion={completion_tokens}, "
                f"prompt={prompt_tokens}, total={total_tokens}"
            )
            
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()