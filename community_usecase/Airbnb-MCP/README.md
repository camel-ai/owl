
# 🏡 CAMEL-AI + MCP: Airbnb Use Case

This example demonstrates how to use the [CAMEL-AI OWL framework](https://github.com/camel-ai/owl) and **MCP (Model Context Protocol)** to search for Airbnb listings using a custom MCP server (`@openbnb/mcp-server-airbnb`). Agents in the OWL framework coordinate to perform tool-augmented travel research in a structured, automated way.

---

## ✨ Use Case

> _“Find me the best Airbnb in Gurugram with a check-in date of 2025-06-01 and a check-out date of 2025-06-07 for 2 adults. Return the top 5 listings with their names, prices, and locations.”_

Agents leverage an MCP server to execute real-time Airbnb queries and return formatted results.

---

## 📦 Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/camel-ai/owl
cd owl
pip install -r requirements.txt
```

---

### 2. Configure MCP Server

In your `mcp_servers_config.json`, add the following:

```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": [
        "-y",
        "@openbnb/mcp-server-airbnb",
        "--ignore-robots-txt"
      ]
    }
  }
}
```

> 🛠️ You will need **Node.js and NPM** installed. Run `npx` will automatically fetch the Airbnb MCP server.

---

### 3. Run the Example Script

```bash
python community_usecase/Airbnb_MCP
```

You can also customize the prompt inside the script itself. Edit the `default_task` section of `Airbnb_MCP.py` like this:

```python
# Replace this line:
default_task = (
    "here you need to add the task"
)

# Example:
default_task = (
    "Find me the best Airbnb in Gurugram with a check-in date of 2025-06-01 "
    "and a check-out date of 2025-06-07 for 2 adults. Return the top 5 listings with their names, "
    "prices, and locations."
)
```

This allows agents to work from your hardcoded task without passing anything via command line.

---

## 🧠 How It Works

- **MCPToolkit** reads the config and connects to the `@openbnb/mcp-server-airbnb`.
- **OWL RolePlaying Agents** simulate a conversation between a `content_curator` and a `research_assistant`.
- The **assistant agent** calls the MCP Airbnb server to fetch listings.
- The results are processed, formatted, and printed.

---

---

## 🚧 Notes

- This script uses **GPT-4o** via OpenAI for both user and assistant roles.
- Supports async execution and graceful cleanup of agents and MCP sessions.
- Add retries and fallback logic for production use.

---

## 📌 References

- [MCP Overview (Anthropic)](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
- [CAMEL-AI GitHub](https://github.com/camel-ai/camel)
- [OWL Framework](https://github.com/camel-ai/owl)
- [MCP Airbnb Plugin](https://www.npmjs.com/package/@openbnb/mcp-server-airbnb)
~~~

