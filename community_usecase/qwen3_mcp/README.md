# 🚀 OWL with Qwen3 MCP Integration

This project demonstrates how to use the [CAMEL-AI OWL framework](https://github.com/camel-ai/owl) with **Qwen3** large language model through MCP (Model Context Protocol). The example showcases improved terminal output formatting, markdown log generation, and seamless integration with MCP servers.

## ✨ Features

- **Enhanced Terminal Output**: Colorful, well-formatted console output for better readability
- **Automatic Log Generation**: Creates detailed markdown logs of agent conversations with timestamps
- **Qwen3 Integration**: Seamlessly uses Qwen3-Plus for both user and assistant agents
- **MCP Server Support**: Connects to MCP servers including EdgeOne Pages and Playwright
- **Robust Error Handling**: Graceful cleanup and exception management

## 📋 Prerequisites

- Python 3.10+
- OWL framework installed
- Qwen API key
- Node.js (for Playwright MCP)

## 🛠️ Setup

1. Clone the OWL repository:
   ```bash
   git clone https://github.com/camel-ai/owl
   cd owl
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add your Qwen API key to the `.env` file:
   ```
   QWEN_API_KEY=your_api_key_here
   ```

4. Configure MCP servers in `mcp_sse_config.json`

5. (Optional) Install Playwright MCP manually:
   ```bash
   npm install -D @playwright/mcp
   ```
   Note: This step is optional as the config will auto-install Playwright MCP through npx.

## 🧩 MCP Servers Included

This example integrates with two powerful MCP servers:

### 1. EdgeOne Pages MCP (`edgeone-pages-mcp`)

EdgeOne Pages MCP is a specialized service that enables:
- **Instant HTML Deployment**: Deploy AI-generated HTML content to EdgeOne Pages with a single call
- **Public Access URLs**: Generate publicly accessible links for deployed content
- **No Setup Required**: Uses an SSE (Server-Sent Events) endpoint, so no local installation is needed

Configuration in `mcp_sse_config.json`:
```json
"edgeone-pages-mcp": {
  "type": "sse",
  "url": "https://mcp.api-inference.modelscope.cn/sse/fcbc9ff4e9704d"
}
```

### 2. Playwright MCP (`playwright`)

Playwright MCP is a powerful browser automation tool that allows:
- **Web Navigation**: Browse websites and interact with web pages
- **Screen Capture**: Take screenshots and extract page content
- **Element Interaction**: Click, type, and interact with page elements
- **Web Scraping**: Extract structured data from web pages

Configuration in `mcp_sse_config.json`:
```json
"playwright": {
  "command": "npx",
  "args": [
    "@playwright/mcp@latest"
  ]
}
```

**Installation Options**: 
1. **Auto-installation**: The configuration above automatically installs and runs Playwright MCP through `npx`.
2. **Manual installation**: If you prefer to install it permanently in your project:
   ```bash
   npm install -D @playwright/mcp
   ```
   Then you can update the config to use the local installation:
   ```json
   "playwright": {
     "command": "npx",
     "args": [
       "@playwright/mcp"
     ]
   }
   ```

## 🚀 Usage

Run the script with a task prompt:

```bash
python run_mcp_qwen3.py "Your task description here"
```

If no task is provided, a default task will be used.

## 📊 Output

1. **Terminal Output**: Colorful, formatted output showing:
   - System messages
   - Task specifications
   - Agent conversations
   - Tool calls
   - Task completion status

2. **Markdown Logs**: Detailed conversation logs saved to `conversation_logs/` directory

## 🔧 Customization

- Modify `mcp_sse_config.json` to add or remove MCP servers
- Adjust model parameters in the `construct_society` function
- Change the maximum conversation rounds with the `round_limit` parameter

## 📝 Technical Details

This implementation extends the standard OWL run_mcp.py script with:

1. Colorized terminal output using Colorama
2. Structured markdown log generation
3. Improved error handling and graceful termination
4. Enhanced formatting for tool calls and agent messages

## 🤝 Acknowledgements

- [CAMEL-AI Organization](https://github.com/camel-ai)
- [OWL Framework](https://github.com/camel-ai/owl)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction)
- [Qwen API](https://help.aliyun.com/zh/dashscope/developer-reference/api-details)
- [EdgeOne Pages](https://edgeone.cloud.tencent.com/pages)
- [Microsoft Playwright](https://github.com/microsoft/playwright-mcp) 