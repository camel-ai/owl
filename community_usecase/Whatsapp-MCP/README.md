# OWL WhatsApp MCP Integration

This project demonstrates a use case connecting **OWL** (from [CAMEL-AI.org](https://camel-ai.org)) with the **WhatsApp MCP Server**. It enables fully automated, agentic replies within messaging apps—without needing predefined workflows or manual tool selection. Simply send a plain message and let the system handle the rest.

---

## Overview

### What It Does

- **Automated, Agentic Messaging:**  
  OWL interacts with the WhatsApp MCP server in real time. Roleplay agents infer the intent behind your messages, automatically selecting the correct toolkit to generate and send responses.

- **Seamless Communication Integration:**  
  This integration demonstrates how intelligent agents can operate across different communication platforms with zero manual orchestration.

### Key Features

- **No Predefined Workflow:**  
  No need for rigid, pre-set procedures. The system dynamically handles each conversation.
  
- **Zero Tool Selection Required:**  
  Simply send a message; the right toolkit is autonomously selected based on the agent’s inference.

- **Real-Time Interaction:**  
  OWL continuously communicates with the WhatsApp MCP server to access message histories, send replies, and manage media files.

---

## Technology Stack

- **OWL Framework:**  
  An open-source multi-agent collaboration framework from [CAMEL-AI](https://github.com/camel-ai/owl).  
- **WhatsApp MCP Server:**  
  An MCP (Model Context Protocol) server that connects directly to WhatsApp via the WhatsApp Web multi-device API. Explore the project on [GitHub](https://github.com/lharries/whatsapp-mcp).

---

## How It Works

1. **Message Processing:**  
   - A plain text message is sent by a user via a messaging app.
   - The OWL framework receives the message and activates roleplay agents.
  
2. **Agent Collaboration:**  
   - Agents, acting in different roles, infer the intent and formulate a response.
   - The appropriate toolkit is dynamically selected.
  
3. **Automated Reply:**  
   - The system communicates in real time with the WhatsApp MCP server.
   - The response is generated and sent back to the messaging app autonomously.

---

## Getting Started

### Prerequisites

- **Go:** Required for the WhatsApp Bridge component.
- **Python 3.6+:** For running the MCP server and OWL integration.
- **UV Package Manager:** Install with:
  ```sh
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **FFmpeg (Optional):** Needed for converting and sending audio messages in the correct format (e.g., .ogg Opus).

### Installation Steps

1. **Clone Repositories:**
   - OWL Framework:  
     ```sh
     git clone https://github.com/camel-ai/owl.git
     ```
   - WhatsApp MCP Server:  
     ```sh
     git clone https://github.com/lharries/whatsapp-mcp.git
     ```

2. **Set Up the WhatsApp Bridge:**
   - Navigate to the WhatsApp bridge directory:
     ```sh
     cd whatsapp-mcp/whatsapp-bridge
     go run main.go
     ```
   - **Authentication:**  
     On first run, scan the provided QR code using your WhatsApp app. (Re-authentication may be required after ~20 days.)

3. **Configure MCP Server Integration:**
   - Create a JSON configuration file (e.g., `claude_desktop_config.json` or `mcp.json`) with the following content (ensure you replace the placeholder paths):
     ```json
     {
       "mcpServers": {
         "whatsapp": {
           "command": "<PATH_TO_UV>",
           "args": [
             "--directory",
             "<PATH_TO_REPO>/whatsapp-mcp/whatsapp-mcp-server",
             "run",
             "main.py"
           ]
         }
       }
     }
     ```
   - Place this file in your Claude Desktop configuration directory or your Cursor configuration directory as appropriate.

4. **Running the OWL MCP Integration:**
   - With the WhatsApp Bridge running and MCP configuration set up, start your OWL-powered agent system:
     ```sh
     python owl/community_usecase/Whatsapp-MCP/app.py
     ```
   - The OWL framework will connect to the MCP server and be ready to process incoming messages.

---

## Deep Dive: MCP & OWL Integration

### MCP Overview
- **What is MCP?**  
  MCP (Model Context Protocol) standardizes communication between AI models and external tools and data sources. Learn more at the [MCP Documentation](https://modelcontextprotocol.io/introduction).

- **Basic Architecture:**  
  MCP uses a client-server model, where a host application communicates with multiple MCP servers to seamlessly access local and remote data sources.

### OWL Framework
- **Role-Playing Agents:**  
  OWL leverages roleplay agents that deconstruct tasks and work collaboratively, ensuring robust automation.
  
- **Real-Time Decision-Making:**  
  Using methods such as POMDP (Partially Observable Markov Decision Processes), OWL optimizes decisions dynamically.

- **Multi-Modal Tool Integration:**  
  From web data scraping to code execution and document processing, OWL integrates various toolkits to empower agent collaboration.

### Code Example Snippet

Below is a simplified version of how to initialize and connect to the MCP toolkit:

```python
from pathlib import Path
from mcp_toolkit import MCPToolkit

# Load configuration and initialize MCP toolkit
config_path = Path(__file__).parent / "mcp_servers_config.json"
mcp_toolkit = MCPToolkit(config_path=str(config_path))

# Establish asynchronous connection
await mcp_toolkit.connect()
```

Then, construct the agent environment and run the task:

```python
question = (
    "I'd like an academic report about Andrew Ng, including his research direction, "
    "published papers, and affiliated institutions. Organize the report in Markdown format and save it to my desktop."
)
tools = list(mcp_toolkit.get_tools())
society = await construct_society(question, tools)
answer, chat_history, token_count = await run_society(society)
print(f"Answer: {answer}")
```

For a complete guide on using MCP with the OWL framework, please refer to [the detailed guide](https://www.camel-ai.org/blogs/owl-mcp-toolkit-practice).

---

## WhatsApp MCP Server Details

- **Capabilities:**
  - **Message Management:** Search, read, and send messages including media (images, videos, documents, audio).
  - **Media Handling:** Supports conversion (with FFmpeg) and downloading of media files.
  
- **Architecture:**
  - **Go WhatsApp Bridge:** Connects to WhatsApp’s Web API, handles QR code authentication, and stores messages locally using SQLite.
  - **Python MCP Server:** Implements the MCP protocol to relay communications between OWL agents and WhatsApp.

- **Installation & Running:**
  - Follow the instructions under the **Installation Steps** section above.
  - Additional details and troubleshooting tips are available in the [WhatsApp MCP GitHub repository](https://github.com/lharries/whatsapp-mcp).

---

## Troubleshooting & FAQs

- **QR Code Not Displaying:**  
  Ensure your terminal supports displaying QR codes, or try restarting the authentication script.

- **Device Limit Issues:**  
  If you reach the maximum number of devices on WhatsApp, remove an existing device from your phone’s linked devices settings.

- **Running on Windows:**  
  For Windows setups, ensure that CGO is enabled and a C compiler (e.g., through MSYS2) is installed. See the [Windows Compatibility Guide](#) for step-by-step instructions.

---

## References & Further Reading

- **MCP Documentation:** [modelcontextprotocol.io](https://modelcontextprotocol.io/introduction)
- **CAMEL-AI MCP:** [camel-ai.org/mcp](https://www.camel-ai.org/mcp)
- **WhatsApp MCP Server Repository:** [GitHub](https://github.com/lharries/whatsapp-mcp)
- **OWL Framework Repository:** [GitHub](https://github.com/camel-ai/owl)

---



