<h1 align="center">
	🦉 OWL: Optimized Workforce Learning for General Multi-Agent Assistance in Real-World Task Automation
	🦉 OWL: 优化劳动力学习的通用智能体，用于处理现实世界的自动化任务
</h1>


<div align="center">

[![文档][docs-image]][docs-url]
[![Discord][discord-image]][discord-url]
[![X][x-image]][x-url]
[![Reddit][reddit-image]][reddit-url]
[![微信][wechat-image]][wechat-url]
[![微信][owl-image]][owl-url]
[![Hugging Face][huggingface-image]][huggingface-url]
[![Star][star-image]][star-url]
[![软件许可证][package-license-image]][package-license-url]


</div>


<hr>

<div align="center">
<h4 align="center">

[English README](https://github.com/camel-ai/owl/tree/main) |
[社区](https://github.com/camel-ai/camel#community) |
[安装](#️-installation) |
[示例](https://github.com/camel-ai/owl/tree/main/owl) |
[论文](https://arxiv.org/abs/2303.17760) |
[引用](#-community) |
[贡献](https://github.com/camel-ai/owl/graphs/contributors) |
[CAMEL-AI](https://www.camel-ai.org/)

</h4>

<div align="center" style="background-color: #f0f7ff; padding: 10px; border-radius: 5px; margin: 15px 0;">
  <h3 style="color: #1e88e5; margin: 0;">
    🏆 OWL 在 GAIA 基准测试中取得 <span style="color: #d81b60; font-weight: bold; font-size: 1.2em;">58.18</span> 平均分，在开源框架中排名 <span style="color: #d81b60; font-weight: bold; font-size: 1.2em;">🏅️ #1</span>！ 🏆
  </h3>
</div>

<div align="center">

🦉 OWL 是一个前沿的多智能体协作框架，推动任务自动化的边界，构建在 [CAMEL-AI Framework](https://github.com/camel-ai/camel)。

我们的愿景是彻底变革 AI 智能体协作解决现实任务的方式。通过利用动态智能体交互，OWL 实现了跨多领域更自然、高效且稳健的任务自动化。

</div>

![](./assets/owl_architecture.png)



<br>


</div>

<!-- # Key Features -->
# 📋 目录

- [📋 目录](#-目录)
- [🔥 新闻](#-新闻)
- [🎬 演示视频](#-演示视频)
- [✨️ 核心功能](#-核心功能)
- [🛠️ 安装](#️-安装)
- [🚀 快速开始](#-快速开始)
- [🧰 工具包与功能](#-工具包与功能)
  - [模型上下文协议 (MCP)](#模型上下文协议-mcp)
- [🌐 网页界面](#-网页界面)
- [🧪 实验](#-实验)
- [⏱️ 未来计划](#️-未来计划)
- [📄 许可证](#-许可证)
- [🖊️ 引用](#️-引用)
- [🤝 贡献](#-贡献)
- [🔥 社区](#-社区)
- [❓ 常见问题](#-常见问题)
- [📚 探索 CAMEL 依赖](#-探索-camel-依赖)
- [⭐ Star History](#-star-history)

# 🔥 新闻

<div align="center" style="background-color: #fffacd; padding: 15px; border-radius: 10px; border: 2px solid #ffd700; margin: 20px 0;">
  <h3 style="color: #d81b60; margin: 0; font-size: 1.3em;">
    🌟🌟🌟 <b>OWL社区用例征集令！</b> 🌟🌟🌟
  </h3>
  <p style="font-size: 1.1em; margin: 10px 0;">
    我们请社区成员贡献创新的OWL用例！<br>
    <b>前十名提交</b>将获得特别社区礼物和认可。
  </p>
  <p>
    <a href="https://github.com/camel-ai/owl/tree/main/community_usecase/COMMUNITY_CALL_FOR_USE_CASES.md" style="background-color: #d81b60; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-weight: bold;">了解更多并提交</a>
  </p>
  <p style="margin: 5px 0;">
    提交截止日期：<b>2025年3月31日</b>
  </p>
</div>

<div align="center" style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; border: 2px solid #4caf50; margin: 20px 0;">
  <h3 style="color: #2e7d32; margin: 0; font-size: 1.3em;">
    🧩 <b>新增：社区智能体挑战！</b> 🧩
  </h3>
  <p style="font-size: 1.1em; margin: 10px 0;">
    展示您的创造力，为AI智能体设计独特的挑战！<br>
    加入我们的社区，见证您的创新想法被尖端AI技术实现。
  </p>
  <p>
    <a href="https://github.com/camel-ai/owl/blob/main/community_challenges.md" style="background-color: #2e7d32; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-weight: bold;">查看与提交挑战</a>
  </p>
</div>

<div style="background-color: #e3f2fd; padding: 12px; border-radius: 8px; border-left: 4px solid #1e88e5; margin: 10px 0;">
  <h4 style="color: #1e88e5; margin: 0 0 8px 0;">
    🎉 最新重大更新 - 2025年3月15日
  </h4>
  <p style="margin: 0;">
    <b>重要改进：</b>
    <ul style="margin: 5px 0 0 0; padding-left: 20px;">
      <li>重构网页用户界面架构，显著提升系统稳定性 🏗️</li>
      <li>优化OWL Agent执行机制，大幅提升性能与效率 🚀</li>
    </ul>
    <i>立即体验全新升级的自动化任务处理能力！</i>
  </p>
</div>

- **[2025.03.27]**: 集成SearxNGToolkit，使用SearxNG搜索引擎执行网络搜索。
- **[2025.03.26]**: 增强Browser Toolkit，支持"chrome"、"msedge"和"chromium"多种浏览器通道。
- **[2025.03.25]**: 支持Gemini 2.5 Pro模型，添加示例运行代码。
- **[2025.03.21]**: 集成OpenRouter模型平台，修复Gemini工具调用的bug。
- **[2025.03.20]**: 在MCP工具包中添加Accept header，支持自动安装playwright。
- **[2025.03.16]**: 支持必应搜索、百度搜索。
- **[2025.03.12]**: 在SearchToolkit中添加了Bocha搜索功能，集成了火山引擎模型平台，并更新了Azure和OpenAI Compatible模型的结构化输出和工具调用能力。
- **[2025.03.11]**: 我们添加了 MCPToolkit、FileWriteToolkit 和 TerminalToolkit，增强了 OWL Agent 的 MCP（模型上下文协议）集成、文件写入能力和终端命令执行功能。MCP 作为一个通用协议层，标准化了 AI 模型与各种数据源和工具的交互方式。
- **[2025.03.09]**: 我们添加了基于网页的用户界面，使系统交互变得更加简便。
- **[2025.03.07]**: 我们开源了 🦉 OWL 项目的代码库。
- **[2025.03.03]**: OWL 在 GAIA 基准测试中取得 58.18 平均分，在开源框架中排名第一！

# 🎬 演示视频

https://private-user-images.githubusercontent.com/55657767/420211368-f29f477d-7eef-46da-8d7a-8f3bcf506da2.mp4

https://private-user-images.githubusercontent.com/55657767/420212194-e813fc05-136a-485f-8df3-f10d9b4e63ec.mp4

此视频演示了如何在本地安装 OWL，展示了它作为一个前沿的多智能体协作框架，推动任务自动化边界的能力：https://www.youtube.com/watch?v=8XlqVyAZOr8

# ✨️ 核心功能

- **在线搜索**：支持多种搜索引擎（包括维基百科、Google、DuckDuckGo、百度、博查等），实现实时信息检索与知识获取
- **多模态处理**：支持互联网或本地视频、图片、语音处理
- **浏览器操作**：借助Playwright框架开发浏览器模拟交互，支持页面滚动、点击、输入、下载、历史回退等功能
- **文件解析**：word、excel、PDF、PowerPoint信息提取，内容转文本/Markdown
- **代码执行**：编写python代码，并使用解释器运行
- **丰富工具包**：提供丰富的工具包，包括ArxivToolkit（学术论文检索）、AudioAnalysisToolkit（音频分析）、CodeExecutionToolkit（代码执行）、DalleToolkit（图像生成）、DataCommonsToolkit（数据共享）、ExcelToolkit（Excel处理）、GitHubToolkit（GitHub交互）、GoogleMapsToolkit（地图服务）、GoogleScholarToolkit（学术搜索）、ImageAnalysisToolkit（图像分析）、MathToolkit（数学计算）、NetworkXToolkit（图形分析）、NotionToolkit（Notion交互）、OpenAPIToolkit（API操作）、RedditToolkit（Reddit交互）、SearchToolkit（搜索服务）、SemanticScholarToolkit（语义学术搜索）、SymPyToolkit（符号计算）、VideoAnalysisToolkit（视频分析）、WeatherToolkit（天气查询）、BrowserToolkit（网页交互）等多种专业工具，满足各类特定任务需求。

# 🛠️ 安装

## 选项1：使用 uv（推荐）

```bash
# 克隆 GitHub 仓库
git clone https://github.com/camel-ai/owl.git

# 进入项目目录
cd owl

# 如果你还没有安装 uv，请先安装
pip install uv

# 创建虚拟环境并安装依赖
# 我们支持使用 Python 3.10、3.11、3.12
uv venv .venv --python=3.10

# 激活虚拟环境
# 对于 macOS/Linux
source .venv/bin/activate
# 对于 Windows
.venv\Scripts\activate

# 安装 CAMEL 及其所有依赖
uv pip install -e .

# 完成后退出虚拟环境
deactivate
```

## 选项2：使用 venv 和 pip

```bash
# 克隆 GitHub 仓库
git clone https://github.com/camel-ai/owl.git

# 进入项目目录
cd owl

# 创建虚拟环境
# 对于 Python 3.10（也适用于 3.11、3.12）
python3.10 -m venv .venv

# 激活虚拟环境
# 对于 macOS/Linux
source .venv/bin/activate
# 对于 Windows
.venv\Scripts\activate

# 从 requirements.txt 安装
pip install -r requirements.txt --use-pep517
```

## 选项3：使用 conda

```bash
# 克隆 GitHub 仓库
git clone https://github.com/camel-ai/owl.git

# 进入项目目录
cd owl

# 创建 conda 环境
conda create -n owl python=3.10

# 激活 conda 环境
conda activate owl

# 选项1：作为包安装（推荐）
pip install -e .

# 选项2：从 requirements.txt 安装
pip install -r requirements.txt --use-pep517

# 完成后退出 conda 环境
conda deactivate
```

## **设置环境变量**

OWL 需要各种 API 密钥来与不同的服务进行交互。`owl/.env_template` 文件包含了所有必要 API 密钥的占位符，以及可以注册这些服务的链接。

### 选项 1：使用 `.env` 文件（推荐）

1. **复制并重命名模板**：
   ```bash
   cd owl
   cp .env_template .env
   ```

2. **配置你的 API 密钥**：
   在你喜欢的文本编辑器中打开 `.env` 文件，并在相应字段中插入你的 API 密钥。
   
   > **注意**：对于最小示例（`examples/run_mini.py`），你只需要配置 LLM API 密钥（例如，`OPENAI_API_KEY`）。

### 选项 2：直接设置环境变量

或者，你可以直接在终端中设置环境变量：

- **macOS/Linux (Bash/Zsh)**：
  ```bash
  export OPENAI_API_KEY="你的-openai-api-密钥"
  ```

- **Windows (命令提示符)**：
  ```batch
  set OPENAI_API_KEY="你的-openai-api-密钥"
  ```

- **Windows (PowerShell)**：
  ```powershell
  $env:OPENAI_API_KEY = "你的-openai-api-密钥"
  ```

> **注意**：直接在终端中设置的环境变量仅在当前会话中有效。

## **使用Docker运行**

OWL可以通过Docker轻松部署，Docker提供了跨不同平台的一致环境。

### **设置说明**

```bash
# 克隆仓库
git clone https://github.com/camel-ai/owl.git
cd owl

# 配置环境变量
cp owl/.env_template owl/.env
# 编辑.env文件，填入您的API密钥
```

### **部署选项**

#### **选项1：使用预构建镜像（推荐）**

```bash
# 此选项从Docker Hub下载一个即用型镜像
# 最快速且推荐给大多数用户
docker-compose up -d

# 在容器中运行OWL
docker-compose exec owl bash
cd .. && source .venv/bin/activate
playwright install-deps
xvfb-python examples/run.py
```

#### **选项2：本地构建镜像**

```bash
# 适用于需要自定义Docker镜像或无法访问Docker Hub的用户：
# 1. 打开docker-compose.yml
# 2. 注释掉"image: mugglejinx/owl:latest"行
# 3. 取消注释"build:"部分及其嵌套属性
# 4. 然后运行：
docker-compose up -d --build

# 在容器中运行OWL
docker-compose exec owl bash
cd .. && source .venv/bin/activate
playwright install-deps
xvfb-python examples/run.py
```

#### **选项3：使用便捷脚本**

```bash
# 导航到容器目录
cd .container

# 使脚本可执行并构建Docker镜像
chmod +x build_docker.sh
./build_docker.sh

# 使用您的问题运行OWL
./run_in_docker.sh "您的问题"
```

### **MCP Desktop Commander设置**

如果在Docker中使用MCP Desktop Commander，请运行：

```bash
npx -y @wonderwhy-er/desktop-commander setup --force-file-protocol
```

更多详细的Docker使用说明，包括跨平台支持、优化配置和故障排除，请参阅 [DOCKER_README.md](.container/DOCKER_README_en.md)

# 🚀 快速开始

## 基本用法
   
运行以下示例：

```bash
python examples/run.py
```

我们还提供了一个最小化示例，只需配置LLM的API密钥即可运行：

```bash
python examples/run_mini.py
```

## 使用不同的模型

### 模型要求

- **工具调用能力**：OWL 需要具有强大工具调用能力的模型来与各种工具包交互。模型必须能够理解工具描述、生成适当的工具调用，并处理工具输出。

- **多模态理解能力**：对于涉及网页交互、图像分析或视频处理的任务，需要具备多模态能力的模型来解释视觉内容和上下文。

#### 支持的模型

有关配置模型的信息，请参阅我们的 [CAMEL 模型文档](https://docs.camel-ai.org/key_modules/models.html#supported-model-platforms-in-camel)。

> **注意**：为获得最佳性能，我们强烈推荐使用 OpenAI 模型（GPT-4 或更高版本）。我们的实验表明，其他模型在复杂任务和基准测试上可能表现明显较差，尤其是那些需要多模态理解和工具使用的任务。

OWL 支持多种 LLM 后端，但功能可能因模型的工具调用和多模态能力而异。您可以使用以下脚本来运行不同的模型：

```bash
# 使用 Qwen 模型运行
python examples/run_qwen_zh.py

# 使用 Deepseek 模型运行
python examples/run_deepseek_zh.py

# 使用 Gemini 模型运行
python examples/run_gemini.py

# 使用其他 OpenAI 兼容模型运行
python examples/run_openai_compatible_model.py

# 使用 Azure OpenAI模型运行
python examples/run_azure_openai.py

# 使用 Ollama 运行
python examples/run_ollama.py
```

你可以通过修改 `examples/run.py` 脚本来运行自己的任务：

```python
# Define your own task
task = "Task description here."

society = construct_society(question)
answer, chat_history, token_count = run_society(society)

print(f"\033[94mAnswer: {answer}\033[0m")
```

上传文件时，只需提供文件路径和问题：

```python
# 处理本地文件（例如，文件路径为 `tmp/example.docx`）
task = "给定的 DOCX 文件中有什么内容？文件路径如下：tmp/example.docx"

society = construct_society(question)
answer, chat_history, token_count = run_society(society)

print(f"答案：{answer}")
```

OWL 将自动调用与文档相关的工具来处理文件并提取答案。

你可以尝试以下示例任务：
- "查询苹果公司的最新股票价格"
- "分析关于气候变化的最新推文情绪"
- "帮我调试这段 Python 代码：[在此粘贴你的代码]"
- "总结这篇研究论文的主要观点：[论文URL]"

# 🧰 工具包与功能

## 模型上下文协议（MCP）

OWL 的 MCP 集成为 AI 模型与各种工具和数据源的交互提供了标准化的方式。
在使用MCP前，需要先安装Node.js。
### **安装 Node.js**
### Windows

下载官方安装包：[Node.js](https://nodejs.org/zh-cn)。

安装时，勾选 "Add to PATH" 选项。

### Linux
```bash
sudo apt update
sudo apt install nodejs npm -y
```
### Mac
```bash
brew install node
```

### **安装 MCP 服务**
```bash
npm install -g @executeautomation/playwright-mcp-server
npx playwright install-deps
```

查看我们的综合示例 `examples/run_mcp.py` 来体验这些功能！

## 可用工具包

> **重要提示**：有效使用工具包需要具备强大工具调用能力的模型。对于多模态工具包（Web、图像、视频），模型还必须具备多模态理解能力。

OWL支持多种工具包，可通过修改脚本中的`tools`列表进行自定义：

```python
# 配置工具包
tools = [
    *BrowserToolkit(headless=False).get_tools(),  # 浏览器自动化
    *VideoAnalysisToolkit(model=models["video"]).get_tools(),
    *AudioAnalysisToolkit().get_tools(),  # 需要OpenAI API密钥
    *CodeExecutionToolkit(sandbox="subprocess").get_tools(),
    *ImageAnalysisToolkit(model=models["image"]).get_tools(),
    SearchToolkit().search_duckduckgo,
    SearchToolkit().search_google,  # 如果不可用请注释
    SearchToolkit().search_wiki,
    SearchToolkit().search_bocha,
    SearchToolkit().search_baidu,
    *ExcelToolkit().get_tools(),
    *DocumentProcessingToolkit(model=models["document"]).get_tools(),
    *FileWriteToolkit(output_dir="./").get_tools(),
]
```

## 主要工具包

关键工具包包括：

### 多模态工具包（需要模型具备多模态能力）
- **BrowserToolkit**：浏览器自动化，用于网页交互和导航
- **VideoAnalysisToolkit**：视频处理和内容分析
- **ImageAnalysisToolkit**：图像分析和解释

### 基于文本的工具包
- **AudioAnalysisToolkit**：音频处理（需要 OpenAI API）
- **CodeExecutionToolkit**：Python 代码执行和评估
- **SearchToolkit**：网络搜索（Google、DuckDuckGo、维基百科）
- **DocumentProcessingToolkit**：文档解析（PDF、DOCX等）

其他专用工具包：ArxivToolkit、GitHubToolkit、GoogleMapsToolkit、MathToolkit、NetworkXToolkit、NotionToolkit、RedditToolkit、WeatherToolkit等。完整工具包列表请参阅[CAMEL工具包文档](https://docs.camel-ai.org/key_modules/tools.html#built-in-toolkits)。

## 自定义配置

自定义可用工具的方法：

```python
# 1. 导入工具包
from camel.toolkits import BrowserToolkit, SearchToolkit, CodeExecutionToolkit

# 2. 配置工具列表
tools = [
    *BrowserToolkit(headless=True).get_tools(),
    SearchToolkit().search_wiki,
    *CodeExecutionToolkit(sandbox="subprocess").get_tools(),
]

# 3. 传递给助手代理
assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}
```

选择必要的工具包可优化性能并减少资源使用。

# 🌐 网页界面

<div align="center" style="background-color: #f0f7ff; padding: 15px; border-radius: 10px; border: 2px solid #1e88e5; margin: 20px 0;">
  <h3 style="color: #1e88e5; margin: 0;">
    🚀 全新升级的网页界面现已发布！
  </h3>
  <p style="margin: 10px 0;">
    体验更稳定的系统性能和优化后的执行效率。
    通过我们直观的界面，开启OWL强大功能的探索之旅！
  </p>
</div>

OWL 现在包含一个基于网页的用户界面，使与系统交互变得更加容易。要启动网页界面，请运行：

```bash
# 中文版本
python owl/webapp_zh.py

# 英文版本
python owl/webapp.py
```

网页界面提供以下功能：

- **便捷的模型选择**：选择不同的模型（OpenAI、Qwen、DeepSeek等）
- **环境变量管理**：直接从界面配置API密钥和其他设置
- **交互式聊天界面**：通过用户友好的界面与OWL智能体交流
- **任务历史**：查看交互的历史记录和结果

网页界面使用Gradio构建，在您的本地机器上运行。除了您配置的模型API调用所需的数据外，不会向外部服务器发送任何数据。

# 🧪 实验

我们提供了一个脚本用于复现 GAIA 上的实验结果。
要复现我们在 GAIA 基准测试中获得的 58.18 分：

1. 切换到 `gaia58.18` 分支：
```bash
git checkout gaia58.18
```

2. 运行评估脚本：
```bash
python examples/run_gaia_roleplaying.py
```

# ⏱️ 未来计划

我们正在不断努力改进 OWL。以下是我们的路线图：

- [ ] 撰写技术博客，详细介绍我们在现实任务中多智能体协作方面的探索与见解
- [ ] 通过引入更多针对特定领域任务的专业工具，进一步完善工具生态系统
- [ ] 开发更复杂的智能体交互模式和通信协议
- [ ] 提高复杂多步推理任务的性能

# 📄 许可证

源代码采用 Apache 2.0 许可证。

# 🖊️ 引用

如果你觉得这个仓库对你有帮助，请引用：


```
@misc{owl2025,
  title        = {OWL: Optimized Workforce Learning for General Multi-Agent Assistance in Real-World Task Automation},
  author       = {{CAMEL-AI.org}},
  howpublished = {\url{https://github.com/camel-ai/owl}},
  note         = {Accessed: 2025-03-07},
  year         = {2025}
}
```

# 🤝 贡献

我们欢迎社区的贡献！以下是您可以提供帮助的方式：

1. 阅读我们的[贡献指南](https://github.com/camel-ai/camel/blob/master/CONTRIBUTING.md)
2. 查看[开放的问题](https://github.com/camel-ai/camel/issues)或创建新的问题
3. 提交包含您改进的拉取请求

**当前开放贡献的问题：**
- [#362](https://github.com/camel-ai/owl/issues/362)
- [#1945](https://github.com/camel-ai/camel/issues/1945)
- [#1925](https://github.com/camel-ai/camel/issues/1925)
- [#1915](https://github.com/camel-ai/camel/issues/1915)

要认领一个问题，只需在该问题下留言表明您的兴趣即可。

# 🔥 社区
加入我们的 ([*Discord*](https://discord.camel-ai.org/) 或 [*微信*](https://ghli.org/camel/wechat.png)) 社区，一起探索智能体扩展规律的边界。

加入我们，参与更多讨论！

![](./assets/community.jpg)

# ❓ 常见问题

**Q: 为什么启动示例脚本后，我没有看到本地运行Chrome浏览器？**

A: 当OWL判断某个任务可以使用非浏览器工具（如搜索、代码分析等）完成时，浏览器就不会启动。只有在判断需要使用浏览器工具的时候，本地才会弹出浏览器窗口，并进行浏览器模拟交互。

**Q: 我应该使用哪个Python版本？**

A: OWL支持Python 3.10、3.11和3.12。为了与所有依赖项获得最佳兼容性，我们推荐使用Python 3.10。

**Q: 我如何为项目做贡献？**

A: 请参阅我们的[贡献](#-贡献)部分，了解如何参与的详细信息。我们欢迎各种形式的贡献，从代码改进到文档更新。

# 📚 探索 CAMEL 依赖

OWL 是基于 [CAMEL](https://github.com/camel-ai/camel) 框架构建的，以下是如何探索 CAMEL 源代码并了解其与 OWL 的工作方式：

## 访问 CAMEL 源代码

```bash
# 克隆 CAMEL 仓库
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
