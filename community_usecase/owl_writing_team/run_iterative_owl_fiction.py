#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import shutil
import datetime
import logging
from typing import Optional, Dict, Any, List, Tuple
import json
import requests
from dotenv import load_dotenv
import re
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

# Hugging Face configuration
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen3-235B-A22B")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.8"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "10000"))

# Iteration configuration - Raised for professional-grade fiction quality
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "8.5"))

def setup_owl_fiction_directories(base_dir: str = "outputs/fiction/iterative_owl") -> Dict[str, Path]:
    """Setup OWL fiction output directory structure with iteration tracking"""
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
        "research": story_dir / story_title / "research",
        "iterations": story_dir / story_title / "iterations",
        "feedback": story_dir / story_title / "feedback"
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
    """Generate text using Hugging Face Chat"""
    try:
        client = Client("tencent/Hunyuan-T1")
        result = client.predict(
                message=prompt,
                api_name="/chat"
        )
        # Print for visibility
        print(result)
            
        return result
            
    except Exception as e:
        logger.error(f"Hugging Face API error: {str(e)}")
        return f"Error: {str(e)}"


def score_content_quality(content: str, criteria: Dict[str, str]) -> Tuple[float, Dict[str, float], str]:
    """Score content quality across multiple dimensions"""
    quality_prompt = f"""
    Evaluate this content on a scale of 1-10 for each criterion:
    
    Content to evaluate:
    {content[:2000]}...
    
    Criteria:
    {json.dumps(criteria, indent=2)}
    
    Provide scores and specific feedback in this JSON format:
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
        result = generate_text(quality_prompt)
        
        # Extract JSON from response with better error handling
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            try:
                json_text = json_match.group()
                # Clean up common JSON formatting issues
                json_text = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', json_text)  # Add quotes around unquoted keys
                json_text = re.sub(r':\s*([^",\[\{][^,\]\}]*)', r': "\1"', json_text)  # Quote unquoted string values
                
                score_data = json.loads(json_text)
                overall_score = score_data.get("overall_score", 5.0)
                dimension_scores = score_data.get("dimension_scores", {})
                feedback = score_data.get("feedback", "") + "\n\nSuggestions:\n" + "\n".join(score_data.get("improvement_suggestions", []))
                return overall_score, dimension_scores, feedback
            except json.JSONDecodeError as je:
                logger.warning(f"JSON parsing failed: {je}, using fallback parsing")
                # Fallback: extract scores and feedback manually
                score_match = re.search(r'overall_score[\'\"]*:\s*([0-9.]+)', result)
                feedback_match = re.search(r'feedback[\'\"]*:\s*[\'\"](.*?)[\'\"]\s*[,}]', result, re.DOTALL)
                
                overall_score = float(score_match.group(1)) if score_match else 5.0
                feedback = feedback_match.group(1) if feedback_match else "Could not parse detailed feedback"
                return overall_score, {}, feedback
        else:
            return 5.0, {}, "Could not find JSON structure in response"
            
    except Exception as e:
        logger.error(f"Error scoring content: {e}")
        return 5.0, {}, f"Error during quality scoring: {str(e)}"

def generate_improvement_prompt(content: str, feedback: str, iteration: int) -> str:
    """Generate improvement prompt based on feedback"""
    return f"""
    CRITICAL: You must generate ACTUAL STORY CONTENT, not instructions or templates.
    
    ITERATION {iteration} IMPROVEMENT TASK:
    
    Previous story content:
    {content[:2000]}...
    
    Quality feedback and areas for improvement:
    {feedback}
    
    REQUIREMENTS:
    1. Write the ACTUAL IMPROVED STORY CONTENT - scenes, dialogue, narrative prose
    2. Address the specific feedback points by rewriting the story portions
    3. Maintain story continuity and character consistency
    4. Do NOT write instructions, templates, or meta-commentary
    5. Do NOT write "Step 1", "Step 2" or generic improvement guidelines
    
    WRITE THE IMPROVED STORY VERSION NOW:
    """

def iterative_content_generation(
    initial_prompt: str, 
    criteria: Dict[str, str], 
    output_dirs: Dict[str, Path],
    step_name: str,
    max_iterations: int = MAX_ITERATIONS
) -> Tuple[str, List[Dict]]:
    """Generate content with iterative improvement based on quality scoring"""
    
    iteration_history = []
    current_content = ""
    
    for iteration in range(max_iterations):
        logger.info(f"Iteration {iteration + 1}/{max_iterations} for {step_name}")
        
        if iteration == 0:
            # First iteration: use original prompt
            prompt = initial_prompt
        else:
            # Subsequent iterations: improve based on feedback
            last_feedback = iteration_history[-1]["feedback"]
            prompt = generate_improvement_prompt(current_content, last_feedback, iteration + 1)
        
        # Generate content using Hugging Face
        content = generate_text(prompt)
        
        # Score the content
        overall_score, dimension_scores, feedback = score_content_quality(content, criteria)
        
        # Record iteration data
        iteration_data = {
            "iteration": iteration + 1,
            "content": content,
            "overall_score": overall_score,
            "dimension_scores": dimension_scores,
            "feedback": feedback,
            "timestamp": datetime.datetime.now().isoformat()
        }
        iteration_history.append(iteration_data)
        
        # Save iteration to file
        write_to_file(
            json.dumps(iteration_data, indent=2),
            f"{step_name}_iteration_{iteration + 1}.json",
            output_dirs["iterations"]
        )
        
        write_to_file(
            content,
            f"{step_name}_iteration_{iteration + 1}.md",
            output_dirs["iterations"]
        )
        
        current_content = content
        
        logger.info(f"{step_name} iteration {iteration + 1} score: {overall_score:.1f}/10")
        
        # Check if quality threshold is met
        if overall_score >= QUALITY_THRESHOLD:
            logger.info(f"{step_name} reached quality threshold ({QUALITY_THRESHOLD}) in {iteration + 1} iterations")
            break
        
        # Don't iterate on the last attempt
        if iteration == max_iterations - 1:
            logger.info(f"{step_name} reached maximum iterations ({max_iterations})")
    
    # Save final feedback summary
    feedback_summary = {
        "step_name": step_name,
        "total_iterations": len(iteration_history),
        "final_score": iteration_history[-1]["overall_score"],
        "improvement": iteration_history[-1]["overall_score"] - iteration_history[0]["overall_score"],
        "iteration_history": iteration_history
    }
    
    write_to_file(
        json.dumps(feedback_summary, indent=2),
        f"{step_name}_feedback_summary.json",
        output_dirs["feedback"]
    )
    
    return current_content, iteration_history

def generate_iterative_owl_story(task: str, output_dirs: Dict[str, Path]) -> str:
    """Generate story content using OWL's iterative approach with quality feedback"""
    
    # Define enhanced quality criteria for each step - Professional publishing standards
    step_criteria = {
        "research": {
            "accuracy": "Exceptional factual accuracy with thorough source verification",
            "relevance": "Highly relevant research that deeply informs story elements",
            "depth": "Comprehensive research covering all story aspects and nuances",
            "creativity": "Creative research insights that enhance story originality"
        },
        "outline": {
            "structure": "Masterful narrative structure with perfect pacing and tension",
            "coherence": "Flawless logical flow with seamless story progression", 
            "engagement": "Compelling plot that captivates readers from start to finish",
            "originality": "Fresh and innovative story structure that surprises readers"
        },
        "characters": {
            "depth": "Profound psychological complexity with multi-layered personalities",
            "believability": "Completely authentic and relatable character development",
            "distinctiveness": "Unforgettable voices that leap off the page",
            "growth": "Meaningful character arcs with transformative journeys"
        },
        "worldbuilding": {
            "consistency": "Flawless internal logic with zero contradictions",
            "immersion": "Rich, sensory details that transport readers completely",
            "originality": "Groundbreaking world concepts that feel fresh and innovative",
            "depth": "Layered world history and culture that feels lived-in"
        },
        "scenes": {
            "pacing": "Perfect rhythm that maintains tension and reader investment",
            "emotion": "Powerful emotional resonance that moves readers deeply",
            "purpose": "Every scene advances plot, character, or theme meaningfully",
            "craft": "Masterful scene construction with vivid, cinematic quality"
        },
        "draft": {
            "prose_quality": "Publication-ready prose with distinctive literary voice",
            "narrative_flow": "Seamless transitions that feel effortless and natural",
            "engagement": "Unputdownable storytelling that compels page-turning",
            "technical_mastery": "Flawless grammar, syntax, and literary technique"
        },
        "revision": {
            "polish": "Professional editorial quality worthy of major publication",
            "consistency": "Perfect consistency in voice, tone, and story elements",
            "impact": "Profound emotional and thematic resonance",
            "marketability": "Commercial appeal with literary merit"
        },
        "final": {
            "excellence": "Award-worthy quality that stands among the best fiction",
            "completion": "Completely satisfying resolution that exceeds expectations",
            "memorability": "Unforgettable story that haunts readers long after",
            "artistry": "Literary artistry that elevates the genre and medium"
        }
    }
    
    steps = [
        {
            "name": "research",
            "prompt": f"Research and gather background information for this story prompt: {task}\n\nProvide relevant context, themes, and potential story elements.",
            "file": ("research", "background_research.md")
        },
        {
            "name": "outline",
            "prompt": "Create a detailed story outline with act structure, plot points, and narrative arc.",
            "file": ("plots", "story_outline.md")
        },
        {
            "name": "characters",
            "prompt": "Develop in-depth character profiles including backstories, motivations, and relationships.",
            "file": ("characters", "character_profiles.md")
        },
        {
            "name": "worldbuilding",
            "prompt": "Create detailed worldbuilding elements, setting descriptions, and atmosphere.",
            "file": ("worldbuilding", "world_details.md")
        },
        {
            "name": "scenes",
            "prompt": "Write detailed scene breakdowns with emotional beats and character interactions.",
            "file": ("scenes", "scene_descriptions.md")
        },
        {
            "name": "draft",
            "prompt": "Write a compelling and engaging first draft incorporating all elements into a cohesive narrative.",
            "file": ("drafts", "first_draft.md")
        },
        {
            "name": "revision",
            "prompt": "Polish and refine the draft, focusing on pacing, dialogue, and emotional impact.",
            "file": ("drafts", "revised_draft.md")
        },
        {
            "name": "final",
            "prompt": "Create the final polished version with enhanced prose and storytelling.",
            "file": ("final", "final_story.md")
        }
    ]
    
    story_content = ""
    current_context = task
    all_iteration_history = {}
    
    for step in steps:
        logger.info(f"Generating {step['name']} with iterative improvement...")
        
        full_prompt = f"""Previous context: {current_context}

Task: {step['prompt']}

Guidelines:
- Maintain consistency with previous elements
- Focus on emotional depth and character development
- Ensure natural flow and pacing
- Create vivid, engaging content

Generate the {step['name']} phase content:"""

        # Use iterative generation with quality feedback
        content, iteration_history = iterative_content_generation(
            full_prompt,
            step_criteria[step['name']],
            output_dirs,
            step['name']
        )
        
        all_iteration_history[step['name']] = iteration_history
        
        # Update context with improved content
        current_context = f"{current_context}\n\n{step['name']}: {content[:500]}..."
        
        # Save the final version to the original location
        dir_key, filename = step['file']
        write_to_file(content, filename, output_dirs[dir_key])
        
        if step['name'] == 'final':
            story_content = content
    
    # Generate overall project summary with iteration statistics
    project_summary = {
        "task": task,
        "timestamp": datetime.datetime.now().isoformat(),
        "iteration_statistics": {},
        "quality_progression": {}
    }
    
    for step_name, history in all_iteration_history.items():
        project_summary["iteration_statistics"][step_name] = {
            "total_iterations": len(history),
            "final_score": history[-1]["overall_score"],
            "initial_score": history[0]["overall_score"],
            "improvement": history[-1]["overall_score"] - history[0]["overall_score"]
        }
        
        project_summary["quality_progression"][step_name] = [
            {"iteration": h["iteration"], "score": h["overall_score"]} 
            for h in history
        ]
    
    write_to_file(
        json.dumps(project_summary, indent=2),
        "project_iteration_summary.json",
        output_dirs["current"]
    )
    
    return story_content

def main():
    """Main function to run iterative OWL fiction writing"""
    if len(sys.argv) < 2:
        print("Usage: python run_iterative_owl_fiction.py 'Your story prompt here'")
        sys.exit(1)

    task = sys.argv[1]
    output_dirs = setup_owl_fiction_directories()
    
    try:
        logger.info(f"Processing fiction task with Iterative OWL: {task}")
        logger.info(f"Max iterations per step: {MAX_ITERATIONS}")
        logger.info(f"Quality threshold: {QUALITY_THRESHOLD}/10")
        
        final_story = generate_iterative_owl_story(task, output_dirs)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        story_title = "_".join(task.lower().split()[:5])
        
        write_to_file(
            f"# Iterative OWL Fiction Project: {task}\n\n{final_story}\n",
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
        
        logger.info(f"Iterative OWL story writing completed successfully")
        logger.info(f"Project files saved to: {output_dirs['current']}")
        logger.info(f"Iteration history saved to: {output_dirs['iterations']}")
        logger.info(f"Quality feedback saved to: {output_dirs['feedback']}")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
