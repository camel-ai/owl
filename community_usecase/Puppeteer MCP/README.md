# 🤖 Puppeteer Task Runner (Streamlit + CAMEL-AI + MCP)

A Streamlit app powered by the [CAMEL-AI OWL framework](https://github.com/camel-ai/owl) and **MCP (Model Context Protocol)** that connects to a Puppeteer-based MCP server. It allows natural language task execution via autonomous agents, combining local tool access with browser automation.

---

## ✨ Features

- **Text-to-action UI**: Enter a task and let the agent figure out how to solve it.
- **OwlRolePlaying Agents**: Multi-agent system using CAMEL-AI to simulate human–AI collaboration.
- **MCP Integration**: Connects to Puppeteer MCP servers for real-world browser-based task execution.
- **Error handling & logs**: Gracefully handles connection issues and provides debug logs.

---

## 📋 Prerequisites

- Python >=3.10,<3.13
- Node.js & npm (for the MCP Puppeteer server plugin)
- A valid OpenAI API key set in your environment:
  ```bash
  export OPENAI_API_KEY="your_api_key_here"
  ```

---

## 🛠️ Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/camel-ai/owl.git
   cd owl/community_usecase/Puppeteer MCP
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate      # macOS/Linux
   venv\\Scripts\\activate     # Windows
   ```

3. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

1. **Environment Variables**  
   Create a `.env` file in the root directory with:
   ```ini
   OPENAI_API_KEY=your_openai_key_here
   ```

2. **MCP Server Config**  
   Ensure `mcp_servers_config.json` is present and contains:
   ```json
   {
     "mcpServers": {
       "puppeteer": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/mcp-server-puppeteer"]
       }
     }
   }
   ```

---

## 🚀 Running the App

Run the Streamlit app:

```bash
streamlit run demo.py
```

This will open the UI in your browser. Enter a natural language task (e.g., “Search for the weather in Paris”) and click **Run Task**.

---

## 🔧 Customization

- **Model config**: Change model types in the `construct_society` function.
- **Prompt behavior**: Adjust task wording, agent roles, or tool combinations as needed.
- **Error handling**: You can improve the exception output area for better UI display.

---

## 📂 Project Structure

```
Puppeteer-MCP/
├── demo.py                   # Streamlit frontend
├── mcp_servers_config.json   # MCP config     
└── .env                      # Secrets and keys
```

---

## 📚 References

- [CAMEL-AI OWL Framework](https://github.com/camel-ai/owl)
- [Anthropic MCP Protocol](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Puppeteer MCP Server (custom)](https://github.com/your-org/mcp-server-puppeteer)

---

*Let your agents browse and automate the web for you!*
