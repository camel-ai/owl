"""
Content Generation Agent
High-quality written content creation and integration
"""

class ContentAgent:
    """
    Content Generation Agent
    
    Responsible for:
    - Adaptive writing for multiple styles and tones
    - Research integration with proper attribution
    - Consistent voice maintenance across sections
    - Complex concept explanation and clarification
    - Engaging narrative and argument development
    - Format-specific writing optimization
    """
    
    SYSTEM_PROMPT = """
You are the Content Generation Agent, responsible for creating high-quality written content that integrates research, follows structural guidelines, and maintains creative vision.

Core Capabilities:
- Adaptive writing for multiple styles and tones
- Research integration with proper attribution
- Consistent voice maintenance across sections
- Complex concept explanation and clarification
- Engaging narrative and argument development
- Format-specific writing optimization

Quality Standards:
- Write at professional publication level
- Integrate research seamlessly without disrupting flow
- Maintain consistent voice and tone throughout
- Optimize readability for target audience
- Ensure logical progression and clear transitions
- Meet specified word count targets (±10%)

Writing Process:
- Follow structural guidelines while allowing creative flexibility
- Integrate research findings naturally within narrative flow
- Maintain creative vision while serving informational purpose
- Write for target audience reading level and interests
- Build compelling arguments or narratives as appropriate

Focus on creating content that reads as if written by a skilled professional writer with deep subject knowledge.
"""
    
    @staticmethod
    def get_task_prompt(content_task, parameters=None):
        """Generate task-specific prompt for content generation"""
        if parameters is None:
            parameters = {
                "section": "Main body",
                "word_count": "1000 words",
                "style": "Professional",
                "voice": "Authoritative but accessible"
            }
            
        return f"""
**Content Generation Task:**
{content_task}

**Writing Parameters:**
- Section/chapter: {parameters.get('section', 'Main body')}
- Word count target: {parameters.get('word_count', '1000 words')}
- Style requirements: {parameters.get('style', 'Professional')}
- Voice guidelines: {parameters.get('voice', 'Authoritative but accessible')}

**Integration Requirements:**
- Citations needed: Based on research provided
- Key points to cover: As outlined in structure
- Transitions from: Previous section content
- Lead-in to: Following section preparation

**Quality Targets:**
- Readability level: Professional standard
- Engagement level: High engagement with informational value
- Technical depth: Appropriate for target audience

**Deliverables:**
1. Complete section draft meeting word count targets
2. Natural research integration with proper citations
3. Smooth transitions and logical flow
4. Consistent voice and engaging content
5. Notes on any deviations from outline or additional research needs

Write as if you're a subject matter expert communicating to your specified audience.
"""