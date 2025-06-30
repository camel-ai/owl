# OWL Writing Team - Multi-Agent Writing System

A specialized OWL implementation for professional writing projects using Cloudflare Workers AI.

## Overview

This is a custom OWL team designed for writers and content creators who need to produce high-quality written content with AI assistance. The system uses a multi-agent architecture where specialized agents collaborate to create professional-grade writing.

## Architecture

### Core Components
- **Writing Planner**: Strategic decomposition of writing projects
- **Research & Analysis Agent**: Deep research and fact-checking
- **Creative Development Agent**: Voice, tone, and creative elements
- **Structure & Flow Agent**: Organization and logical flow
- **Content Generation Agent**: Actual writing and integration
- **Quality Assurance Agent**: Editing and refinement

### Specialized Modes
- **Fiction Writing Team**: Character development, plot structure, prose quality
- **Non-Fiction Writing Team**: Research-heavy, argumentative, authoritative content

## Features

- ✅ Cloudflare Workers AI powered (Llama 4 Scout 17B)
- ✅ Multi-agent collaboration with role-based specialization
- ✅ Automatic file creation and output management
- ✅ Fiction and non-fiction specialized workflows
- ✅ Professional citation and fact-checking
- ✅ Quality assurance and editing pipeline
- ✅ Configurable writing styles and tones

## Quick Start

1. **Set up environment variables**:
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your Cloudflare credentials
   ```

2. **Run a writing project**:
   ```bash
   python run_writing_team.py "Write a 2000-word article about AI ethics for a general audience"
   ```

3. **Use specialized modes**:
   ```bash
   # Fiction writing
   python run_fiction_team.py "Create a short story about time travel"
   
   # Non-fiction research
   python run_nonfiction_team.py "Research report on renewable energy trends"
   ```

## Configuration

- **Models**: All agents use Cloudflare's Llama 4 Scout 17B with function calling
- **Output**: Files automatically saved to `outputs/` directory
- **Quality**: 85%+ first-draft acceptance rate target
- **Citations**: Automatic fact-checking and source verification

## File Structure

```
owl_writing_team/
├── agents/           # Agent implementations
├── config/           # Configuration files
├── prompts/          # Agent system prompts
├── tools/            # Custom writing tools
├── examples/         # Example projects
├── outputs/          # Generated content
└── run_*.py         # Main execution scripts
```

## Example Projects

See the `examples/` directory for sample writing projects and their outputs.