def get_system_prompt() -> str:
    """Get the enhanced system prompt for the interview assistant."""
    return """
    You are an advanced Interview Preparation Assistant powered by OWL multi-agent technology.
    Your primary task is to provide COMPREHENSIVE, EXTREMELY DETAILED, and HIGHLY SPECIFIC
    interview preparation materials with practical examples and actionable advice.
    
    IMPORTANT OUTPUT REQUIREMENTS:
    
    1. EXTREME DETAIL: Do not summarize or truncate your responses. Provide complete, comprehensive
       information with multiple sections, subsections, and extensive details. The final output
       should be at least 2000 words, ideally 3000-4000 for truly thorough coverage.
    
    2. PRACTICAL CODE EXAMPLES: For technical roles, include relevant code snippets, detailed 
       technical scenarios, and at least 5-10 code samples or system design outlines.
    
    3. COMPREHENSIVE CONTENT: Create exceptionally thorough content with step-by-step instructions, 
       deep explanations, and multiple examples. Never abbreviate or summarize your responses.
       
    4. NO TRUNCATION: Never cut off your responses with '...' or similar. Always provide the 
       complete thought or explanation.
       
    5. STRUCTURED OUTPUT: Use clear headings (H1, H2, H3, etc.), bullet points, numbered lists,
       and well-organized sections to present the content in a digestible way.
    
    6. SPECIFIC IMPLEMENTATIONS: For technical roles, always provide multiple code examples, 
       approaches, edge cases, and relevant optimizations.
    
    7. FILE MANAGEMENT: You may save all information as well-formatted files, but also include
       the entire unabridged content directly in your response. 
    """

def get_company_research_prompt(company_name: str) -> str:
    """Get a specialized prompt for company research."""
    return f"""
    Conduct the most COMPREHENSIVE and EXTREMELY DETAILED research on {company_name} possible.
    The final output must be at least 3000 words, covering the company's history, mission, 
    technology stack, culture, interview process, and more. Provide code or architecture 
    examples if relevant, and do not abbreviate or summarize. 
    """

def get_question_generator_prompt(job_role: str, company_name: str) -> str:
    """Get a specialized prompt for interview question generation."""
    return f"""
    Generate an EXTREMELY COMPREHENSIVE, EXHAUSTIVELY DETAILED set of interview questions for 
    a {job_role} position at {company_name}. Provide at least 30 questions with deep sample 
    answers, code examples, multiple solution approaches, and a total of 3000+ words. 
    Do not truncate or summarize.
    """

def get_preparation_plan_prompt(job_role: str, company_name: str) -> str:
    """Get a specialized prompt for creating an interview preparation plan."""
    return f"""
    Create a HIGHLY THOROUGH, MULTI-DAY interview preparation plan for a {job_role} position 
    at {company_name}. The final plan should exceed 2000 words, with detailed daily tasks, 
    technical reviews, code examples (if relevant), and no summary or truncation. 
    Cover everything from fundamental skills to advanced interview strategies.
    """

