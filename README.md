<h1 align="center">
	🦉 OWL: Optimized Workforce Learning for General Multi-Agent Assistance in Real-World Task Automation
</h1>


<div align="center">

[![Documentation][docs-image]][docs-url]
[![Discord][discord-image]][discord-url]
[![X][x-image]][x-url]
[![Reddit][reddit-image]][reddit-url]
[![Wechat][wechat-image]][wechat-url]
[![Wechat][owl-image]][owl-url]
[![Hugging Face][huggingface-image]][huggingface-url]
[![Star][star-image]][star-url]
[![Package License][package-license-image]][package-license-url]


</div>


<hr>

<div align="center">
<h4 align="center">

[中文阅读](https://github.com/camel-ai/owl/tree/main/README_zh.md) |
[Community](https://github.com/camel-ai/owl#community) |
[Installation](#️-installation) |
[Examples](https://github.com/camel-ai/owl/tree/main/owl) |
[Paper](https://arxiv.org/abs/2303.17760) |
[Technical Report](https://hypnotic-mind-6bd.notion.site/OWL-Optimized-Workforce-Learning-for-General-Multi-Agent-Assistance-in-Real-World-Task-Automation-1d4004aeb21380158749c7f84b20643f) |
[Citation](https://github.com/camel-ai/owl#citation) |
[Contributing](https://github.com/camel-ai/owl/graphs/contributors) |
[CAMEL-AI](https://www.camel-ai.org/)

</h4>

<div align="center" style="background-color: #f0f7ff; padding: 10px; border-radius: 5px; margin: 15px 0;">
  <h3 style="color: #1e88e5; margin: 0;">
    🏆 OWL achieves <span style="color: #d81b60; font-weight: bold; font-size: 1.2em;">69.09</span> average score on GAIA benchmark and ranks <span style="color: #d81b60; font-weight: bold; font-size: 1.2em;">🏅️ #1</span> among open-source frameworks! 🏆
  </h3>
</div>

<div align="center">

🦉 OWL is a cutting-edge framework for multi-agent collaboration that pushes the boundaries of task automation, built on top of the [CAMEL-AI Framework](https://github.com/camel-ai/camel).

<!-- OWL achieves **58.18** average score on [GAIA](https://huggingface.co/spaces/gaia-benchmark/leaderboard) benchmark and ranks 🏅️ #1 among open-source frameworks. -->

Our vision is to revolutionize how AI agents collaborate to solve real-world tasks. By leveraging dynamic agent interactions, OWL enables more natural, efficient, and robust task automation across diverse domains.

</div>

![](./assets/owl_architecture.png)

<br>


</div>

<!-- # Key Features -->
# 📋 Table of Contents

- [📋 Table of Contents](#-table-of-contents)
- [🔥 News](#-news)
- [🎬 Demo Video](#-demo-video)
- [✨️ Core Features](#️-core-features)
- [🛠️ Installation](#️-installation)
- [🚀 Quick Start](#-quick-start)
- [🧰 Toolkits and Capabilities](#-toolkits-and-capabilities)
  - [Model Context Protocol (MCP)](#model-context-protocol-mcp)
- [🌐 Web Interface](#-web-interface)
- [🧪 Experiments](#-experiments)
- [⏱️ Future Plans](#️-future-plans)
- [📄 License](#-license)
- [🖊️ Cite](#️-cite)
- [🤝 Contributing](#-contributing)
- [🔥 Community](#-community)
- [❓ FAQ](#-faq)
- [📚 Exploring CAMEL Dependency](#-exploring-camel-dependency)
- [⭐ Star History](#-star-history)

# 🔥 News


<div align="center" style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; border: 2px solid #4caf50; margin: 20px 0;">
  <h3 style="color: #2e7d32; margin: 0; font-size: 1.3em;">
    🧩 <b>NEW: COMMUNITY AGENT CHALLENGES!</b> 🧩
  </h3>
  <p style="font-size: 1.1em; margin: 10px 0;">
    Showcase your creativity by designing unique challenges for AI agents! <br>
    Join our community and see your innovative ideas tackled by cutting-edge AI.
  </p>
  <p>
    <a href="https://github.com/camel-ai/owl/blob/main/community_challenges.md" style="background-color: #2e7d32; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-weight: bold;">View & Submit Challenges</a>
  </p>
</div>

<div style="background-color: #e3f2fd; padding: 12px; border-radius: 8px; border-left: 4px solid #1e88e5; margin: 10px 0;">
  <h4 style="color: #1e88e5; margin: 0 0 8px 0;">
    🎉 Latest Major Update - March 15, 2025
  </h4>
  <p style="margin: 0;">
    <b>Significant Improvements:</b>
    <ul style="margin: 5px 0 0 0; padding-left: 20px;">
      <li>Restructured web-based UI architecture for enhanced stability 🏗️</li>
      <li>Optimized OWL Agent execution mechanisms for better performance 🚀</li>
    </ul>
    <i>Try it now and experience the improved performance in your automation tasks!</i>
  </p>
</div>

- **[2025.04.18]**: We uploaded OWL's new GAIA benchmark score of **69.09%**, ranking #1 among open-source frameworks. Check the technical report [here](https://hypnotic-mind-6bd.notion.site/OWL-Optimized-Workforce-Learning-for-General-Multi-Agent-Assistance-in-Real-World-Task-Automation-1d4004aeb21380158749c7f84b20643f).
- **[2025.03.27]**: Integrate SearxNGToolkit performing web searches using SearxNG search engine.
- **[2025.03.26]**: Enhanced Browser Toolkit with multi-browser support for "chrome", "msedge", and "chromium" channels.
- **[2025.03.25]**: Supported Gemini 2.5 Pro, added example run code
- **[2025.03.21]**: Integrated OpenRouter model platform, fix bug with Gemini tool calling.
- **[2025.03.20]**: Accept header in MCP Toolkit, support automatic playwright installation.
- **[2025.03.16]**: Support Bing search, Baidu search.
- **[2025.03.12]**: Added Bocha search in SearchToolkit, integrated Volcano Engine model platform, and enhanced Azure and OpenAI Compatible models with structured output and tool calling.
- **[2025.03.11]**: We added MCPToolkit, FileWriteToolkit, and TerminalToolkit to enhance OWL agents with MCP tool calling, file writing capabilities, and terminal command execution.
- **[2025.03.09]**: We added a web-based user interface that makes it easier to interact with the system.
- **[2025.03.07]**: We open-sourced the codebase of the 🦉 OWL project.
- **[2025.03.03]**: OWL achieved the #1 position among open-source frameworks on the GAIA benchmark with a score of 58.18.


# 🎬 Demo Video

https://github.com/user-attachments/assets/2a2a825d-39ea-45c5-9ba1-f9d58efbc372

https://private-user-images.githubusercontent.com/55657767/420212194-e813fc05-136a-485f-8df3-f10d9b4e63ec.mp4

This video demonstrates how to install OWL locally and showcases its capabilities as a cutting-edge framework for multi-agent collaboration: https://www.youtube.com/watch?v=8XlqVyAZOr8

# ✨️ Core Features

- **Online Search**: Support for multiple search engines (including Wikipedia, Google, DuckDuckGo, Baidu, Bocha, etc.) for real-time information retrieval and knowledge acquisition.
- **Multimodal Processing**: Support for handling internet or local videos, images, and audio data.
- **Browser Automation**: Utilize the Playwright framework for simulating browser interactions, including scrolling, clicking, input handling, downloading, navigation, and more.
- **Document Parsing**: Extract content from Word, Excel, PDF, and PowerPoint files, converting them into text or Markdown format.
- **Code Execution**: Write and execute Python code using interpreter.
- **Built-in Toolkits**: Access to a comprehensive set of built-in toolkits including:
  - **Model Context Protocol (MCP)**: A universal protocol layer that standardizes AI model interactions with various tools and data sources
  - **Core Toolkits**: ArxivToolkit, AudioAnalysisToolkit, CodeExecutionToolkit, DalleToolkit, DataCommonsToolkit, ExcelToolkit, GitHubToolkit, GoogleMapsToolkit, GoogleScholarToolkit, ImageAnalysisToolkit, MathToolkit, NetworkXToolkit, NotionToolkit, OpenAPIToolkit, RedditToolkit, SearchToolkit, SemanticScholarToolkit, SymPyToolkit, VideoAnalysisToolkit, WeatherToolkit, BrowserToolkit, and many more for specialized tasks

# 🛠️ Installation

## **Prerequisites**

### Install Python
Before installing OWL, ensure you have Python installed (version 3.10, 3.11, or 3.12 is supported):

```bash
# Check if Python is installed
python --version

# If not installed, download and install from https://www.python.org/downloads/
# For macOS users with Homebrew:
brew install python@3.10

# For Ubuntu/Debian:
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

## **Installation Options**

OWL supports multiple installation methods to fit your workflow preferences.

### Option 1: Using uv (Recommended)

```bash
# Clone github repo
git clone https://github.com/camel-ai/owl.git

# Change directory into project directory
cd owl

# Install uv if you don't have it already
pip install uv

# Create a virtual environment and install dependencies
uv venv .venv --python=3.10

# Activate the virtual environment
# For macOS/Linux
source .venv/bin/activate
# For Windows
.venv\Scripts\activate

# Install CAMEL with all dependencies
uv pip install -e .
```

### Option 2: Using venv and pip

```bash
# Clone github repo
git clone https://github.com/camel-ai/owl.git

# Change directory into project directory
cd owl

# Create a virtual environment
# For Python 3.10 (also works with 3.11, 3.12)
python3.10 -m venv .venv

# Activate the virtual environment
# For macOS/Linux
source .venv/bin/activate
# For Windows
.venv\Scripts\activate

# Install from requirements.txt
pip install -r requirements.txt --use-pep517
```

### Option 3: Using conda

```bash
# Clone github repo
git clone https://github.com/camel-ai/owl.git

# Change directory into project directory
cd owl

# Create a conda environment
conda create -n owl python=3.10

# Activate the conda environment
conda activate owl

# Option 1: Install as a package (recommended)
pip install -e .

# Option 2: Install from requirements.txt
pip install -r requirements.txt --use-pep517
```

### Option 4: Using Docker

#### **Using Pre-built Image (Recommended)**

```bash
# This option downloads a ready-to-use image from Docker Hub
# Fastest and recommended for most users
docker compose up -d

# Run OWL inside the container
docker compose exec owl bash
cd .. && source .venv/bin/activate
playwright install-deps
xvfb-python examples/run.py
```

#### **Building Image Locally**

```bash
# For users who need to customize the Docker image or cannot access Docker Hub:
# 1. Open docker-compose.yml
# 2. Comment out the "image: mugglejinx/owl:latest" line
# 3. Uncomment the "build:" section and its nested properties
# 4. Then run:
docker compose up -d --build

# Run OWL inside the container
docker compose exec owl bash
cd .. && source .venv/bin/activate
playwright install-deps
xvfb-python examples/run.py
```

#### **Using Convenience Scripts**

```bash
# Navigate to container directory
cd .container

# Make the script executable and build the Docker image
chmod +x build_docker.sh
./build_docker.sh

# Run OWL with your question
./run_in_docker.sh "your question"
```

## **Setup Environment Variables**

OWL requires various API keys to interact with different services.

### Setting Environment Variables Directly

You can set environment variables directly in your terminal:

- **macOS/Linux (Bash/Zsh)**:
  ```bash
  export OPENAI_API_KEY="your-openai-api-key-here"
  # Add other required API keys as needed
  ```

- **Windows (Command Prompt)**:
  ```batch
  set OPENAI_API_KEY=your-openai-api-key-here
  ```

- **Windows (PowerShell)**:
  ```powershell
  $env:OPENAI_API_KEY = "your-openai-api-key-here"
  ```

> **Note**: Environment variables set directly in the terminal will only persist for the current session.

### Alternative: Using a `.env` File

If you prefer using a `.env` file instead, you can:

1. **Copy and Rename the Template**:
   ```bash
   # For macOS/Linux
   cd owl
   cp .env_template .env
   
   # For Windows
   cd owl
   copy .env_template .env
   ```

   Alternatively, you can manually create a new file named `.env` in the owl directory and copy the contents from `.env_template`.

2. **Configure Your API Keys**:
   Open the `.env` file in your preferred text editor and insert your API keys in the corresponding fields.

> **Note**: For the minimal example (`examples/run_mini.py`), you only need to configure the LLM API key (e.g., `OPENAI_API_KEY`).

### **MCP Desktop Commander Setup**

If using MCP Desktop Commander within Docker, run:

```bash
npx -y @wonderwhy-er/desktop-commander setup --force-file-protocol
```

For more detailed Docker usage instructions, including cross-platform support, optimized configurations, and troubleshooting, please refer to [DOCKER_README.md](.container/DOCKER_README_en.md).

# 🚀 Quick Start

## Basic Usage

After installation and setting up your environment variables, you can start using OWL right away:

```bash
python examples/run.py
```

## Running with Different Models

### Model Requirements

- **Tool Calling**: OWL requires models with robust tool calling capabilities to interact with various toolkits. Models must be able to understand tool descriptions, generate appropriate tool calls, and process tool outputs.

- **Multimodal Understanding**: For tasks involving web interaction, image analysis, or video processing, models with multimodal capabilities are required to interpret visual content and context.

#### Supported Models

For information on configuring AI models, please refer to our [CAMEL models documentation](https://docs.camel-ai.org/key_modules/models.html#supported-model-platforms-in-camel).

> **Note**: For optimal performance, we strongly recommend using OpenAI models (GPT-4 or later versions). Our experiments show that other models may result in significantly lower performance on complex tasks and benchmarks, especially those requiring advanced multi-modal understanding and tool use.

OWL supports various LLM backends, though capabilities may vary depending on the model's tool calling and multimodal abilities. You can use the following scripts to run with different models:

```bash
# Run with Qwen model
python examples/run_qwen_zh.py

# Run with Deepseek model
python examples/run_deepseek_zh.py

# Run with other OpenAI-compatible models
python examples/run_openai_compatible_model.py

# Run with Gemini model
python examples/run_gemini.py

# Run with Azure OpenAI
python examples/run_azure_openai.py

# Run with Ollama
python examples/run_ollama.py
```

For a simpler version that only requires an LLM API key, you can try our minimal example:

```bash
python examples/run_mini.py
```

You can run OWL agent with your own task by modifying the `examples/run.py` script:

```python
# Define your own task
task = "Task description here."

society = construct_society(question)
answer, chat_history, token_count = run_society(society)

print(f"\033[94mAnswer: {answer}\033[0m")
```

For uploading files, simply provide the file path along with your question:

```python
# Task with a local file (e.g., file path: `tmp/example.docx`)
task = "What is in the given DOCX file? Here is the file path: tmp/example.docx"

society = construct_society(question)
answer, chat_history, token_count = run_society(society)
print(f"\033[94mAnswer: {answer}\033[0m")
```

OWL will then automatically invoke document-related tools to process the file and extract the answer.


### Example Tasks

Here are some tasks you can try with OWL:

- "Find the latest stock price for Apple Inc."
- "Analyze the sentiment of recent tweets about climate change"
- "Help me debug this Python code: [your code here]"
- "Summarize the main points from this research paper: [paper URL]"
- "Create a data visualization for this dataset: [dataset path]"

# 🧰 Toolkits and Capabilities

## Model Context Protocol (MCP)

OWL's MCP integration provides a standardized way for AI models to interact with various tools and data sources:

Before using MCP, you need to install Node.js first.
### **Install Node.js**
### Windows

Download the official installer: [Node.js](https://nodejs.org/en).

Check "Add to PATH" option during installation.

### Linux
```bash
sudo apt update
sudo apt install nodejs npm -y
```
### Mac
```bash
brew install node
```

### **Install Playwright MCP Service**
```bash
npm install -g @executeautomation/playwright-mcp-server
npx playwright install-deps
```

Try our comprehensive MCP examples:
- `examples/run_mcp.py` - Basic MCP functionality demonstration (local call, requires dependencies)
- `examples/run_mcp_sse.py` - Example using the SSE protocol (Use remote services, no dependencies)

## Available Toolkits

> **Important**: Effective use of toolkits requires models with strong tool calling capabilities. For multimodal toolkits (Web, Image, Video), models must also have multimodal understanding abilities.

OWL supports various toolkits that can be customized by modifying the `tools` list in your script:

```python
# Configure toolkits
tools = [
    *BrowserToolkit(headless=False).get_tools(),  # Browser automation
    *VideoAnalysisToolkit(model=models["video"]).get_tools(),
    *AudioAnalysisToolkit().get_tools(),  # Requires OpenAI Key
    *CodeExecutionToolkit(sandbox="subprocess").get_tools(),
    *ImageAnalysisToolkit(model=models["image"]).get_tools(),
    SearchToolkit().search_duckduckgo,
    SearchToolkit().search_google,  # Comment out if unavailable
    SearchToolkit().search_wiki,
    SearchToolkit().search_bocha,
    SearchToolkit().search_baidu,
    *ExcelToolkit().get_tools(),
    *DocumentProcessingToolkit(model=models["document"]).get_tools(),
    *FileWriteToolkit(output_dir="./").get_tools(),
]
```

## Available Toolkits

Key toolkits include:

### Multimodal Toolkits (Require multimodal model capabilities)
- **BrowserToolkit**: Browser automation for web interaction and navigation
- **VideoAnalysisToolkit**: Video processing and content analysis
- **ImageAnalysisToolkit**: Image analysis and interpretation

### Text-Based Toolkits
- **AudioAnalysisToolkit**: Audio processing (requires OpenAI API)
- **CodeExecutionToolkit**: Python code execution and evaluation
- **SearchToolkit**: Web searches (Google, DuckDuckGo, Wikipedia)
- **DocumentProcessingToolkit**: Document parsing (PDF, DOCX, etc.)

Additional specialized toolkits: ArxivToolkit, GitHubToolkit, GoogleMapsToolkit, MathToolkit, NetworkXToolkit, NotionToolkit, RedditToolkit, WeatherToolkit, and more. For a complete list, see the [CAMEL toolkits documentation](https://docs.camel-ai.org/key_modules/tools.html#built-in-toolkits).

## Customizing Your Configuration

To customize available tools:

```python
# 1. Import toolkits
from camel.toolkits import BrowserToolkit, SearchToolkit, CodeExecutionToolkit

# 2. Configure tools list
tools = [
    *BrowserToolkit(headless=True).get_tools(),
    SearchToolkit().search_wiki,
    *CodeExecutionToolkit(sandbox="subprocess").get_tools(),
]

# 3. Pass to assistant agent
assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}
```

Selecting only necessary toolkits optimizes performance and reduces resource usage.

# 🌐 Web Interface

<div align="center" style="background-color: #f0f7ff; padding: 15px; border-radius: 10px; border: 2px solid #1e88e5; margin: 20px 0;">
  <h3 style="color: #1e88e5; margin: 0;">
    🚀 Enhanced Web Interface Now Available!
  </h3>
  <p style="margin: 10px 0;">
    Experience improved system stability and optimized performance with our latest update.
    Start exploring the power of OWL through our user-friendly interface!
  </p>
</div>

## Starting the Web UI

```bash
# Start the Chinese version
python owl/webapp_zh.py

# Start the English version
python owl/webapp.py

# Start the Japanese version
python owl/webapp_jp.py
```

## Features

- **Easy Model Selection**: Choose between different models (OpenAI, Qwen, DeepSeek, etc.)
- **Environment Variable Management**: Configure your API keys and other settings directly from the UI
- **Interactive Chat Interface**: Communicate with OWL agents through a user-friendly interface
- **Task History**: View the history and results of your interactions

The web interface is built using Gradio and runs locally on your machine. No data is sent to external servers beyond what's required for the model API calls you configure.

# 🧪 Experiments

To reproduce OWL's GAIA benchmark score of 58.18:

1. Switch to the `gaia58.18` branch:
   ```bash
   git checkout gaia58.18
   ```

2. Run the evaluation script:
   ```bash
   python run_gaia_roleplaying.py
   ```

This will execute the same configuration that achieved our top-ranking performance on the GAIA benchmark.

# ⏱️ Future Plans

We're continuously working to improve OWL. Here's what's on our roadmap:

- [ ] Write a technical blog post detailing our exploration and insights in multi-agent collaboration in real-world tasks
- [ ] Enhance the toolkit ecosystem with more specialized tools for domain-specific tasks
- [ ] Develop more sophisticated agent interaction patterns and communication protocols
- [ ] Improve performance on complex multi-step reasoning tasks

# 📄 License

The source code is licensed under Apache 2.0.

# 🖊️ Cite

If you find this repo useful, please cite:


```
@misc{owl2025,
  title={OWL: Optimized Workforce Learning for General Multi-Agent Assistance in Real-World Task Automation},
  author={Mengkang Hu, Yuhang Zhou, Wendong Fan, Yuzhou Nie, Bowei Xia, Tao Sun, Ziyu Ye, Zhaoxuan Jin, Yingru Li, Zeyu Zhang, Yifeng Wang, Qianshuo Ye, Ping Luo, Guohao Li},
  url={https://github.com/camel-ai/owl},
  year={2025}
}
```

# 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

1. Read our [Contribution Guidelines](https://github.com/camel-ai/camel/blob/master/CONTRIBUTING.md)
2. Check [open issues](https://github.com/camel-ai/camel/issues) or create new ones
3. Submit pull requests with your improvements

**Current Issues Open for Contribution:**
- [#1915](https://github.com/camel-ai/camel/issues/1915)
- [#2190](https://github.com/camel-ai/camel/issues/2190)
- [#2165](https://github.com/camel-ai/camel/issues/2165)
- [#2121](https://github.com/camel-ai/camel/issues/2121)
- [#1908](https://github.com/camel-ai/camel/issues/1908)
- [#1538](https://github.com/camel-ai/camel/issues/1538)
- [#1481](https://github.com/camel-ai/camel/issues/1481)

To take on an issue, simply leave a comment stating your interest.

# 🔥 Community
Join us ([*Discord*](https://discord.camel-ai.org/) or [*WeChat*](https://ghli.org/camel/wechat.png)) in pushing the boundaries of finding the scaling laws of agents. 

Join us for further discussions!
<!-- ![](./assets/community.png) -->
![](./assets/community.jpeg)

# ❓ FAQ

**Q: Why don't I see Chrome running locally after starting the example script?**

A: If OWL determines that a task can be completed using non-browser tools (such as search or code execution), the browser will not be launched. The browser window will only appear when OWL determines that browser-based interaction is necessary.

**Q: Which Python version should I use?**

A: OWL supports Python 3.10, 3.11, and 3.12. 

**Q: How can I contribute to the project?**

A: See our [Contributing](#-contributing) section for details on how to get involved. We welcome contributions of all kinds, from code improvements to documentation updates.

# 📚 Exploring CAMEL Dependency

OWL is built on top of the [CAMEL](https://github.com/camel-ai/camel) Framework, here's how you can explore the CAMEL source code and understand how it works with OWL:

## Accessing CAMEL Source Code

```bash
# Clone the CAMEL repository
git clone https://github.com/camel-ai/camel.git
cd camel
```

# ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=camel-ai/owl&type=Date)](https://star-history.com/#camel-ai/owl&Date)



[docs-image]: https://img.shields.io/badge/Documentation-EB3ECC
[docs-url]: https://camel-ai.github.io/camel/index.html
[star-image]: https://img.shields.io/github/stars/camel-ai/owl?label=stars&logo=github&color=brightgreen
[star-url]: https://github.com/camel-ai/owl/stargazers
[package-license-image]: https://img.shields.io/badge/License-Apache_2.0-blue.svg
[package-license-url]: https://github.com/camel-ai/owl/blob/main/licenses/LICENSE

[colab-url]: https://colab.research.google.com/drive/1AzP33O8rnMW__7ocWJhVBXjKziJXPtim?usp=sharing
[colab-image]: https://colab.research.google.com/assets/colab-badge.svg
[huggingface-url]: https://huggingface.co/camel-ai
[huggingface-image]: https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-CAMEL--AI-ffc107?color=ffc107&logoColor=white
[discord-url]: https://discord.camel-ai.org/
[discord-image]: https://img.shields.io/discord/1082486657678311454?logo=discord&labelColor=%20%235462eb&logoColor=%20%23f5f5f5&color=%20%235462eb
[wechat-url]: https://ghli.org/camel/wechat.png
[wechat-image]: https://img.shields.io/badge/WeChat-CamelAIOrg-brightgreen?logo=wechat&logoColor=white
[x-url]: https://x.com/CamelAIOrg
[x-image]: https://img.shields.io/twitter/follow/CamelAIOrg?style=social
[twitter-image]: https://img.shields.io/twitter/follow/CamelAIOrg?style=social&color=brightgreen&logo=twitter
[reddit-url]: https://www.reddit.com/r/CamelAI/
[reddit-image]: https://img.shields.io/reddit/subreddit-subscribers/CamelAI?style=plastic&logo=reddit&label=r%2FCAMEL&labelColor=white
[ambassador-url]: https://www.camel-ai.org/community
[owl-url]: ./assets/qr_code.jpg
[owl-image]: https://img.shields.io/badge/WeChat-OWLProject-brightgreen?logo=wechat&logoColor=white
