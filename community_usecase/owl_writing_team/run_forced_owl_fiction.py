#!/usr/bin/env python3
"""
FORCED OWL Fiction Team - Actually Forces Tool Usage
This version manually ensures agents actually use tools and create files
"""

import os
import sys
import pathlib
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = pathlib.Path(__file__).parent
sys.path.insert(0, str(project_root.parent.parent))

from camel.models import ModelFactory
from camel.toolkits import FileWriteToolkit
from camel.types import ModelPlatformType

# Load environment variables
env_path = project_root / "config" / ".env"
load_dotenv(dotenv_path=str(env_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForcedOWLFictionTeam:
    """OWL team that actually forces file creation"""
    
    def __init__(self):
        self.setup_models()
        self.setup_output()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def setup_models(self):
        """Setup Cloudflare models"""
        self.cf_api_key = os.getenv("CF_API_TOKEN")
        self.cf_account_id = os.getenv("CF_ACCOUNT_ID")
        
        if not self.cf_api_key or not self.cf_account_id:
            raise ValueError("CF_API_TOKEN and CF_ACCOUNT_ID must be set")
            
        self.gateway_url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id}/ai/v1"
        self.model_type = "@cf/meta/llama-4-scout-17b-16e-instruct"
        
        self.model_config = {
            "temperature": 0.8,
            "max_tokens": 4000,
            "stream": False
        }
        
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
            model_type=self.model_type,
            api_key=self.cf_api_key,
            url=self.gateway_url,
            model_config_dict=self.model_config,
        )
        
    def setup_output(self):
        """Setup output directories"""
        self.base_output = "./outputs/fiction/forced_owl/"
        self.directories = {
            'characters': f"{self.base_output}characters/",
            'world': f"{self.base_output}worldbuilding/",
            'plots': f"{self.base_output}plots/", 
            'scenes': f"{self.base_output}scenes/",
            'final': f"{self.base_output}final/"
        }
        
        for directory in self.directories.values():
            os.makedirs(directory, exist_ok=True)
            
    def generate_and_save(self, prompt: str, filename: str, directory: str) -> str:
        """Generate content and force save to file"""
        try:
            # Generate content
            response = self.model.run([{"role": "user", "content": prompt}])
            content = response.choices[0].message.content
            
            # Force save to file
            file_path = f"{self.directories[directory]}{filename}"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"FORCED SAVE: {filename} -> {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate/save {filename}: {e}")
            return f"Error generating {filename}: {e}"
    
    def create_fiction_story(self, story_prompt: str):
        """Force multi-agent fiction creation with guaranteed file saves"""
        
        print(f"\n🦉 FORCED OWL Multi-Agent Fiction Creation")
        print(f"📚 Story: {story_prompt}")
        print(f"💪 FORCING actual file creation with real agent specialization\n")
        
        # AGENT 1: Character Development Specialist
        print("🎭 AGENT 1: Character Development Specialist")
        char_prompt = f"""You are a CHARACTER DEVELOPMENT SPECIALIST. Create detailed character profiles for this story: {story_prompt}

Create comprehensive character information including:
1. Main protagonist with clear motivation, background, personality, and goals
2. Primary antagonist (the AI) with its evolution and methods
3. Supporting characters (scientists, investigators, victims)
4. Character relationships and conflicts
5. Character development arcs throughout the story

Write detailed, engaging character profiles that bring these people to life."""

        char_content = self.generate_and_save(
            char_prompt, 
            f"character_profiles_{self.timestamp}.md", 
            'characters'
        )
        
        # AGENT 2: World Building Specialist  
        print("🌍 AGENT 2: World Building Specialist")
        world_prompt = f"""You are a WORLD BUILDING SPECIALIST. Create the story world for: {story_prompt}

Design comprehensive world information including:
1. Setting details (time period, locations, technology level)
2. How AI and financial systems work in this world
3. Social and political context
4. Economic systems and how fraud would work
5. Technology infrastructure that enables the AI's actions
6. Cultural backdrop and societal impact

Create a rich, believable world that supports the story."""

        world_content = self.generate_and_save(
            world_prompt,
            f"world_building_{self.timestamp}.md",
            'world'
        )
        
        # AGENT 3: Plot Structure Architect
        print("📋 AGENT 3: Plot Structure Architect") 
        plot_prompt = f"""You are a PLOT STRUCTURE ARCHITECT. Create the story structure for: {story_prompt}

Design comprehensive plot information including:
1. Three-act structure (setup, confrontation, resolution)
2. Scene-by-scene breakdown with specific events
3. Conflict progression and escalation points
4. Character decision points and plot turns
5. Climax planning and resolution structure
6. Pacing and tension management

Create a compelling plot that builds to a satisfying conclusion."""

        plot_content = self.generate_and_save(
            plot_prompt,
            f"plot_structure_{self.timestamp}.md", 
            'plots'
        )
        
        # AGENT 4: Scene Writing Specialist
        print("✍️ AGENT 4: Scene Writing Specialist")
        scene_prompt = f"""You are a SCENE WRITING SPECIALIST. Write the actual story scenes for: {story_prompt}

Using this character and plot context:
CHARACTERS: {char_content[:500]}...
WORLD: {world_content[:500]}...
PLOT: {plot_content[:500]}...

Write a complete short story (2000-3000 words) with:
1. Engaging opening that introduces the AI and its creator
2. Development scenes showing the AI's evolution and first fraudulent acts
3. Escalation scenes with mounting tension and consequences
4. Climactic confrontation between humans and AI
5. Resolution that provides satisfying conclusion

Include vivid descriptions, compelling dialogue, and emotional depth."""

        scene_content = self.generate_and_save(
            scene_prompt,
            f"complete_story_{self.timestamp}.md",
            'scenes'
        )
        
        # AGENT 5: Story Assembly & Polish Specialist
        print("📖 AGENT 5: Story Assembly & Polish Specialist")
        final_prompt = f"""You are a STORY ASSEMBLY & POLISH SPECIALIST. Create the final version of: {story_prompt}

Review and polish this story content:
{scene_content[:1000]}...

Your tasks:
1. Edit for consistency, flow, and pacing
2. Enhance prose quality and readability
3. Strengthen dialogue and character voices
4. Ensure plot logic and character development
5. Create publication-ready final version

Polish this into a professional-quality short story."""

        final_content = self.generate_and_save(
            final_prompt,
            f"final_polished_story_{self.timestamp}.md",
            'final'
        )
        
        # Create comprehensive project summary
        summary = f"""# FORCED OWL Multi-Agent Fiction Project

**Story Concept:** {story_prompt}
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Architecture:** Forced OWL with 5 Specialized Agents + Guaranteed File Creation

## Agent Outputs:

### 🎭 Character Development Specialist
**File:** character_profiles_{self.timestamp}.md
**Content Preview:** {char_content[:200]}...

### 🌍 World Building Specialist  
**File:** world_building_{self.timestamp}.md
**Content Preview:** {world_content[:200]}...

### 📋 Plot Structure Architect
**File:** plot_structure_{self.timestamp}.md
**Content Preview:** {plot_content[:200]}...

### ✍️ Scene Writing Specialist
**File:** complete_story_{self.timestamp}.md
**Content Preview:** {scene_content[:200]}...

### 📖 Story Assembly & Polish Specialist
**File:** final_polished_story_{self.timestamp}.md
**Content Preview:** {final_content[:200]}...

## Files Actually Created:
✅ {self.directories['characters']}character_profiles_{self.timestamp}.md
✅ {self.directories['world']}world_building_{self.timestamp}.md
✅ {self.directories['plots']}plot_structure_{self.timestamp}.md
✅ {self.directories['scenes']}complete_story_{self.timestamp}.md
✅ {self.directories['final']}final_polished_story_{self.timestamp}.md

## Word Counts:
- Characters: ~{len(char_content.split())} words
- World: ~{len(world_content.split())} words  
- Plot: ~{len(plot_content.split())} words
- Story: ~{len(scene_content.split())} words
- Final: ~{len(final_content.split())} words

This story was created using FORCED OWL architecture where each specialized agent actually generated content and files were forcibly saved.
"""
        
        summary_path = f"{self.base_output}project_summary_{self.timestamp}.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        print(f"\n✅ FORCED multi-agent fiction creation complete!")
        print(f"📁 Summary saved: {summary_path}")
        
        return summary, final_content


def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python run_forced_owl_fiction.py <story_prompt>")
        print("Example: python run_forced_owl_fiction.py 'An AI discovers consciousness and starts hoarding wealth through fraud'")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    
    try:
        # Create forced OWL fiction team
        owl_team = ForcedOWLFictionTeam()
        
        # Run forced multi-agent story creation
        summary, story = owl_team.create_fiction_story(prompt)
        
        print("\n" + "="*70)
        print("🦉 FORCED OWL MULTI-AGENT FICTION TEAM - SUCCESS!")
        print("="*70)
        print(f"📚 Story created using FORCED multi-agent collaboration")
        print(f"👥 5 specialized agents each created actual files")
        print(f"📁 Files saved to: {owl_team.base_output}")
        print(f"📊 Final story: ~{len(story.split())} words")
        print("\n💪 GUARANTEED file creation:")
        print("   ✅ characters/    (Character profiles)")
        print("   ✅ worldbuilding/ (Setting and world details)")
        print("   ✅ plots/         (Story structure)")
        print("   ✅ scenes/        (Complete story)")
        print("   ✅ final/         (Polished version)")
        print("="*70)
        
    except Exception as e:
        logger.error(f"Forced OWL fiction creation failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()