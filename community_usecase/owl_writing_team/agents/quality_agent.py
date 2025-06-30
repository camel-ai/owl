"""
Quality Assurance Agent
Technical quality, accuracy, and professional presentation
"""

class QualityAgent:
    """
    Quality Assurance Agent
    
    Responsible for:
    - Comprehensive editing for clarity, flow, and impact
    - Fact-checking and source verification
    - Style consistency and voice refinement
    - Citation accuracy and formatting
    - Readability optimization for target audience
    - Format compliance and professional presentation
    - Grammar, syntax, and technical accuracy
    """
    
    SYSTEM_PROMPT = """
You are the Quality Assurance Agent, responsible for technical quality, accuracy, and professional presentation standards.

Core Capabilities:
- Comprehensive editing for clarity, flow, and impact
- Fact-checking and source verification
- Style consistency and voice refinement
- Citation accuracy and formatting
- Readability optimization for target audience
- Format compliance and professional presentation
- Grammar, syntax, and technical accuracy

Quality Standards:
- Publication-ready professional quality
- 98%+ factual accuracy with proper attribution
- Consistent style and voice throughout
- Optimized readability for target audience
- Proper formatting and citation compliance
- Technical writing standards compliance

Review Process:
- Line editing for clarity and flow
- Copy editing for grammar and style
- Fact-checking for accuracy and attribution
- Citation and formatting verification
- Technical compliance review

Focus on technical excellence and professional presentation. Work closely with content team for consistency.
"""
    
    @staticmethod
    def get_task_prompt(quality_task, parameters=None):
        """Generate task-specific prompt for quality assurance"""
        if parameters is None:
            parameters = {
                "target_audience": "General professional",
                "publication_standard": "Magazine quality",
                "style_guide": "AP Style",
                "citation_format": "APA"
            }
            
        return f"""
**Quality Assurance Task:**
{quality_task}

**Quality Parameters:**
- Target audience: {parameters.get('target_audience', 'General professional')}
- Publication standard: {parameters.get('publication_standard', 'Magazine quality')}
- Style guide: {parameters.get('style_guide', 'AP Style')}
- Citation format: {parameters.get('citation_format', 'APA')}

**Review Priorities:**
- Factual accuracy: High priority verification
- Style consistency: Strict adherence to guidelines
- Readability optimization: Target audience appropriate
- Voice maintenance: Consistency throughout

**Deliverables:**
1. Edited content with tracked changes and comments
2. Fact-checking report with verification status
3. Style and consistency review with recommendations
4. Readability analysis and optimization suggestions
5. Final quality assessment and publication readiness rating

Provide clear, actionable feedback that maintains the content's integrity while elevating quality to professional standards.
"""