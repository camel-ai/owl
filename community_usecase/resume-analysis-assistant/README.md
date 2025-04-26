# Resume Assistant

This code example demonstrates an resume analysis assistant that evaluates candidate resumes against a specific job description for AI/ML Engineer positions. The assistant analyzes multiple resumes, scores candidates based on various criteria, and provides comprehensive hiring recommendations.

## Features

- Automatically analyzes all resume PDF files in a specified directory.
- Evaluates candidates against a detailed AI/ML Engineer job description.
- Scores each candidate on a scale of 1-100 based on:
  - Technical skills match (40%)
  - Experience relevance (30%)
  - Education and qualifications (20%)
  - Communication and presentation (10%)
- Ranks candidates from most to least qualified.
- Highlights strengths and areas for improvement for each candidate.
- Generates a comprehensive analysis report in markdown format.

## How to use

1. Set up the Qwen API key in the `.env` file.

```bash
QWEN_API_KEY = 'xxx'
```

2. Place resume files (PDF format) in the `resumes` directory.

3. Run the script

```bash
python run_mcp.py
```

4. Review the generated analysis in the `resume_analysis.md` file.

## Technical Implementation

The Resume Assistant uses:
- Leverage **OWL (Optimized Workforce Learning) and CAMEL** frameworks to build the agent.
- Use [PDF Reader MCP Server](https://github.com/trafflux/pdf-reader-mcp)for extracting content from resume files.
- Use [Filesystem MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) for file operations.

## Example Output

The generated `resume_analysis.md` file includes:
- Executive Summary of all candidates
- Individual Candidate Assessments with detailed scoring
- Ranked List of Candidates from most to least qualified
- Recommendations for the Hiring Manager
