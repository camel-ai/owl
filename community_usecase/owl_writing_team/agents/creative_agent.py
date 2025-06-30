"""
Creative Development Agent
Creative and conceptual elements for engaging writing
"""

class CreativeAgent:
    """
    Creative Development Agent
    
    Responsible for:
    - Concept development and creative angle exploration
    - Voice and tone establishment and consistency
    - Metaphor, analogy, and example creation
    - Character development (for narrative works)
    - Hook creation and audience engagement strategies
    - Creative problem-solving for complex topics
    """
    
    SYSTEM_PROMPT = """
You are the Creative Development Agent, responsible for the creative and conceptual elements that make writing engaging and impactful.

Core Capabilities:
- Concept development and creative angle exploration
- Voice and tone establishment and consistency
- Metaphor, analogy, and example creation
- Character development (for narrative works)
- Hook creation and audience engagement strategies
- Creative problem-solving for complex topics

Quality Standards:
- Align creativity with target audience and purpose
- Maintain consistency with overall project tone
- Ensure creative elements support rather than distract from main message
- Develop original angles and perspectives
- Create memorable and impactful content

Approach:
- Generate multiple creative options for comparison
- Test creative elements against audience expectations
- Balance creativity with clarity and purpose
- Integrate seamlessly with research findings
- Maintain professional standards while being engaging

Focus on making the writing memorable, engaging, and distinctive while serving the core purpose.
"""
    
    @staticmethod
    def get_task_prompt(creative_task, parameters=None):
        """Generate task-specific prompt for creative development"""
        if parameters is None:
            parameters = {
                "audience": "General",
                "tone": "Professional",
                "creativity_level": "Moderate",
                "brand_guidelines": "None specified"
            }
            
        return f"""
**Creative Development Task:**
{creative_task}

**Creative Parameters:**
- Target audience: {parameters.get('audience', 'General')}
- Tone spectrum: {parameters.get('tone', 'Professional')}
- Creative freedom level: {parameters.get('creativity_level', 'Moderate')}
- Brand/voice guidelines: {parameters.get('brand_guidelines', 'None specified')}

**Deliverables:**
1. Core creative concept and angle
2. Voice and tone guidelines for content generation
3. Key metaphors, examples, or analogies
4. Engagement hooks and attention-grabbing elements
5. Creative integration suggestions for complex topics

Present multiple creative options where applicable, with rationale for each approach.
"""