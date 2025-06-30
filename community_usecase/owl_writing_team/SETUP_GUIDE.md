# OWL Writing Team - Setup Guide

## Prerequisites

1. **Python 3.8+** installed on your system
2. **Cloudflare Workers AI Account** with API access
3. **CAMEL Framework** (should be available from parent OWL installation)

## Quick Setup

### 1. Environment Configuration

Copy and configure your environment variables:

```bash
cd community_usecase/owl_writing_team
cp config/.env.example config/.env
```

Edit `config/.env` with your Cloudflare credentials:

```bash
# Required: Get these from your Cloudflare dashboard
CF_API_TOKEN=your_cloudflare_api_token_here
CF_ACCOUNT_ID=your_cloudflare_account_id_here

# Optional: Customize writing behavior
DEFAULT_WRITING_MODE=professional
DEFAULT_TARGET_AUDIENCE=general
MIN_FIRST_DRAFT_ACCEPTANCE=85
```

### 2. Get Cloudflare Credentials

1. **Sign up for Cloudflare** at https://cloudflare.com
2. **Go to AI Gateway** in your dashboard
3. **Create a new Gateway** (if you don't have one)
4. **Get your Account ID** from the dashboard sidebar
5. **Create an API Token**:
   - Go to "My Profile" → "API Tokens"
   - Create token with "AI Gateway:Read" permissions
   - Copy the token

### 3. Test Installation

Run a quick test to verify everything works:

```bash
# Test general writing
python run_writing_team.py "Write a short article about the benefits of AI"

# Test fiction writing
python run_fiction_team.py "A robot learns to dream"

# Test non-fiction research
python run_nonfiction_team.py "The future of renewable energy"
```

## Advanced Configuration

### Model Customization

Edit `config/.env` to customize models for different writing types:

```bash
# Use different models for different writing types
FICTION_MODEL=@cf/meta/llama-4-scout-17b-16e-instruct
NONFICTION_MODEL=@cf/meta/llama-4-scout-17b-16e-instruct
RESEARCH_MODEL=@cf/meta/llama-4-scout-17b-16e-instruct

# Adjust creativity vs accuracy
FICTION_TEMPERATURE=0.8      # Higher for creativity
NONFICTION_TEMPERATURE=0.3   # Lower for accuracy
```

### Output Management

Customize where files are saved:

```python
# In your script
writing_team = OWLWritingTeam()
writing_team.output_dir = "./my_custom_output/"
```

### Quality Settings

Adjust quality thresholds:

```bash
MIN_FIRST_DRAFT_ACCEPTANCE=85    # Minimum quality score (%)
REQUIRED_SOURCE_ACCURACY=98      # Fact-checking accuracy (%)
ENABLE_CRITICAL_REVIEW=true     # Enable rigorous review
ENABLE_FACT_CHECKING=true       # Enable fact verification
```

## Usage Examples

### Basic Usage

```bash
# General writing (articles, blogs, content)
python run_writing_team.py "Your writing prompt here"

# Fiction writing (stories, novels, scripts)
python run_fiction_team.py "Your story idea here"

# Non-fiction research (reports, analyses, papers)
python run_nonfiction_team.py "Your research topic here"
```

### Advanced Usage

```bash
# Specify content type
python run_writing_team.py "AI ethics guide" "technical_guide"
python run_fiction_team.py "Time travel romance" "novella"
python run_nonfiction_team.py "Climate change analysis" "white_paper"
```

### Programmatic Usage

```python
from run_writing_team import OWLWritingTeam

# Initialize team
team = OWLWritingTeam()

# Run project
result, history, tokens = team.run_writing_project(
    "Write about sustainable technology",
    project_type="article"
)

print(f"Completed in {len(history)} rounds using {tokens} tokens")
```

## Troubleshooting

### Common Issues

**"CF_API_TOKEN not found"**
- Make sure your `.env` file is in the `config/` directory
- Verify the token is correctly copied (no extra spaces)

**"Model not available"**
- Check your Cloudflare AI Gateway has the model enabled
- Try using a different model in your `.env` file

**"No files created"**
- Check the `outputs/` directory permissions
- Verify the agents are actually calling file writing tools (check logs)

**"Low quality output"**
- Increase the round limit: `run_writing_project(prompt, round_limit=40)`
- Adjust temperature settings in `.env`
- Enable critical review: `ENABLE_CRITICAL_REVIEW=true`

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your writing team code here
```

### Performance Optimization

For faster execution:
- Use shorter prompts for initial testing
- Reduce round limits for simple projects
- Use backup models for non-critical content

For higher quality:
- Increase round limits (30-50 rounds)
- Enable all quality checks
- Use primary models only

## File Output Structure

Your completed projects will be organized like this:

```
outputs/
├── general/          # General writing projects
│   ├── drafts/
│   ├── research/
│   └── final/
├── fiction/          # Fiction projects
│   ├── characters/
│   ├── worldbuilding/
│   ├── plots/
│   └── drafts/
└── nonfiction/       # Research projects
    ├── research/
    ├── sources/
    ├── arguments/
    └── final/
```

Each project creates:
- **Draft files**: Work-in-progress content
- **Research files**: Source materials and fact-checking
- **Final files**: Polished, publication-ready content
- **Summary files**: Project overview and process documentation

## Next Steps

1. **Run Examples**: Try the example scripts in `examples/`
2. **Customize Prompts**: Edit agent prompts in `agents/` for your needs
3. **Add Tools**: Extend functionality by adding new tools
4. **Monitor Quality**: Review output files and adjust settings
5. **Scale Up**: Use for larger, production writing projects

## Support

- Check logs for detailed error information
- Review the main OWL documentation for framework details
- Ensure all dependencies are properly installed