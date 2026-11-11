# 🗂️ Filesystem Task Runner (Streamlit + OWL + Filesystem MCP)

A Streamlit app powered by the [CAMEL-AI OWL framework](https://github.com/camel-ai/owl) and **MCP (Model Context Protocol)** that connects to a filesystem-based MCP server. It allows natural language task execution via autonomous agents, enabling file management, editing, and exploration using simple prompts.

---

## ✨ Features

- **Natural language interface**: Describe your file system task and let agents take care of it.
- **Multi-agent roleplay**: Uses `OwlRolePlaying` to simulate interactions between user and assistant agents.
- **Filesystem MCP Integration**: Communicates with an MCP server that exposes filesystem tools like read/write/search/edit/move.
- **Debug logs and error reporting**: Transparent error display and detailed tracebacks in the UI.

---

## 📋 Prerequisites

- Python >=3.10,<3.13
- Node.js (for MCP server)
- Docker (optional, for running the server)
- A valid OpenAI API key:
  ```bash
  export OPENAI_API_KEY="your_openai_key_here"
  ```

---

## 🛠️ Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/camel-ai/owl.git
   cd owl/community_usecase/File_System_MCP
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS/Linux
   venv\\Scripts\\activate.bat     # Windows
   ```

3. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the MCP filesystem server**

   **Using Docker:**

   ```bash
   docker build -t mcp/filesystem -f src/filesystem/Dockerfile .
   docker run -i --rm \
     --mount type=bind,src=/your/data,path=/projects \
     mcp/filesystem /projects
   ```

   **Or with NPX:**

   ```bash
   npx -y @modelcontextprotocol/server-filesystem /your/data
   ```

---

## ⚙️ Configuration

1. **Environment Variables**

   Create a `.env` file with:
   ```ini
   OPENAI_API_KEY=your_openai_key_here
   ```

2. **MCP Server Config**

   `mcp_servers_config.json` should look like:

   ```json
   {
     "mcpServers": {
       "filesystem": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-filesystem",
           "/absolute/path/to/your/data"
         ]
       }
     }
   }
   ```

---

## 🚀 Running the App

Launch the Streamlit UI:

```bash
streamlit run demo.py
```

Enter a task like:

> "Create a new file named report.txt and write 'Q2 sales increased by 20%'."

Then click **Run Task** to let the agents execute it.

---

## 🔧 Customization

- **Agent behavior**: Modify the `construct_society` function in `demo.py`.
- **Tools**: Add custom tools to the `tools` list from `MCPToolkit` or define new ones.
- **Models**: Adjust OpenAI model type or temperature in the `ModelFactory.create()` calls.

---

## 📂 Project Structure

```
filesystem-task-runner/
├── demo.py                    # Streamlit interface
├── mcp_servers_config.json    # MCP server configuration
├── .env                       # Environment variables
└── README.md
```

---

## 📚 References

- [CAMEL-AI OWL Framework](https://github.com/camel-ai/owl)
- [Anthropic MCP Protocol](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Filesystem MCP Server](https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem)

---

*Let your agents manipulate the filesystem for you!*
