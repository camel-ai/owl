# 🦉 Interview Preparation Assistant

An intelligent multi-agent interview preparation system powered by the OWL framework that helps you prepare for job interviews with comprehensive research, tailored questions, and detailed preparation plans.

![Interview Preparation Assistant](https://github.com/parthshr370/owl/blob/community_usecase/parthshr370/community_usecase/OWL%20Interview%20Preparation%20Assistant/Screenshot_20250321_201930.png?raw=true)

## ✨ Features

- **🔍 Company Research**: Automatically researches companies using real-time web data
- **❓ Interview Question Generation**: Creates tailored interview questions specific to your job role and target company
- **📋 Preparation Plans**: Builds comprehensive step-by-step interview preparation plans
- **🧠 AI-Powered Agents**: Leverages multiple AI agents to work together on your interview preparation
- **💻 Code Examples**: Provides code examples for technical roles with explanations
- **🔄 Real-time Progress**: Shows conversation process between AI agents as they prepare your materials

## 📋 Table of Contents

- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)

## 🛠 Requirements

- Python 3.10+ (tested on Python 3.10)
- Access to one of the following AI models:
  - OpenAI API (GPT-4)
  - OpenRouter API (Gemini models)
- Internet connection for web search and company research
- Minimum 8GB RAM

## 🚀 Installation

### 1. Clone the OWL Repository

First, clone the OWL repository, which this project depends on:

```bash
git clone https://github.com/camel-ai/owl.git
cd owl
```

### 2. Create a Virtual Environment

```bash
# Create a conda environment (recommended)
conda create -n interview_assistant python=3.10
conda activate interview_assistant

# OR using venv
python -m venv interview_env
source interview_env/bin/activate  # On Windows: interview_env\Scripts\activate
```

### 3. Install OWL and Dependencies

```bash
# Install OWL
pip install -e .

# Install additional dependencies
pip install streamlit numpy pandas opencv-python
```

### 4. Configure API Keys

Create a `.env` file in the project directory with your API keys:

```bash
# Navigate to the Interview Preparation Assistant directory
cd community_usecase/new\ int/

# Create .env file
touch .env
```

Add your API keys to the `.env` file:

```
# OpenAI API (recommended for best results)
OPENAI_API_KEY=your_openai_api_key_here

# OR OpenRouter API (for access to Gemini models)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: Google Search API for enhanced research (optional)
GOOGLE_API_KEY=your_google_api_key_here
SEARCH_ENGINE_ID=your_google_search_engine_id_here
```

## ⚡ Quick Start

The fastest way to get started is to use the Streamlit web interface:

```bash
# Navigate to the project directory
cd community_usecase/new\ int/

# Start the web application
streamlit run app.py
```

This will open a web browser window with the Interview Preparation Assistant interface where you can:

1. Enter your target job role (e.g., "Machine Learning Engineer")
2. Enter your target company name (e.g., "Google")
3. Generate interview preparation materials

## 📚 Usage Guide

### Web Interface

The web interface provides three main functions:

#### 1. Company Research

Click on "Research Company" to generate a comprehensive report about your target company including:
- Company background and culture
- Technical stack and technologies used
- Interview process and expectations
- Key products and services


#### 2. Interview Questions

Click on "Generate Questions" to create tailored interview questions for your role and company:
- Technical questions with code examples
- Behavioral questions specific to the company culture
- Role-specific questions to showcase your expertise 
- Sample answers and solution approaches


#### 3. Preparation Plan

Click on "Create Preparation Plan" to receive a detailed day-by-day preparation guide:
- Structured preparation timeline
- Technical topics to review
- Practice exercises and code challenges
- Research and preparation tasks
- Interview day tips


### Command Line Usage

You can also run specific functions from the command line:

```bash
# Run company research
python -c "from main import research_company; result = research_company('Google', detailed=True); print(result['answer'])"

# Generate interview questions
python -c "from main import generate_interview_questions; result = generate_interview_questions('Machine Learning Engineer', 'Google'); print(result['answer'])"

# Create preparation plan
python -c "from main import create_interview_prep_plan; result = create_interview_prep_plan('Machine Learning Engineer', 'Google'); print(result['answer'])"
```

### Log Monitoring

You can view the logs in real-time in the "System Logs" tab of the web interface to monitor:
- AI agent conversations
- Progress of each request
- Any errors or issues that occur

## ⚙️ Configuration

### Customizing Parameters

You can adjust the following parameters in `main.py`:

1. **Round Limit**: Change the conversation round limit by modifying the `round_limit` parameter in function calls (default: 5)

2. **Model Selection**: Edit the model configuration in `construct_interview_assistant()` to use different models

3. **Output Directory**: Change `INTERVIEW_PREP_DIR` to customize where results are stored

### Environment Variables

In addition to API keys, you can customize behavior with these environment variables:

- `LOG_LEVEL`: Set to `DEBUG`, `INFO`, `WARNING`, or `ERROR` to control logging verbosity

## 🔧 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure your API keys are correctly set in the `.env` file
   - Check that you're using the correct format without quotes or extra spaces

2. **Model Errors**
   - If using OpenRouter, ensure the model specified is available on your account
   - Verify you have sufficient API credits for your requests

3. **Round Limit Not Working**
   - The system enforces a strict limit of 5 conversation rounds to prevent excessive token usage
   - You can adjust this in the code if needed, but may encounter higher API costs

4. **Memory Errors**
   - Processing large contexts can require significant memory
   - Try using a machine with more RAM or reducing model context sizes

### Getting Help

If you encounter issues not covered here:

1. Check the logs in the "System Logs" tab of the web interface
2. Examine the console output for error messages
3. File an issue on the GitHub repository

## 📂 Project Structure

```
community_usecase/new int/
├── app.py                   # Streamlit web interface
├── main.py                  # Core functionality and API connections
├── config/
│   └── prompts.py           # Prompt templates for different tasks
├── interview_prep/          # Generated interview preparation materials
├── logging_utils.py         # Logging utilities
└── README.md                # This documentation
```

## 📝 License

This project is built on top of the CAMEL-AI OWL framework, which is licensed under the Apache License 2.0.

## 🙏 Acknowledgements

- This project is built on the [CAMEL-AI OWL framework](https://github.com/camel-ai/owl)
- Special thanks to the contributors of CAMEL-AI for making multi-agent AI systems accessible

---

Made with ❤️ for job seekers everywhere.
