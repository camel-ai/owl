# Notion Integration with OWL

This project demonstrates the integration of Notion with OWL (Optimized Workforce Learning) using the official Notion MCP server. It provides automated interaction with Notion workspaces through AI agents.

## Prerequisites

- Python 3.10+
- Node.js and npm
- CAMEL framework installed
- A Notion account and integration

## Installation

#### 1. Clone this repository:
   ```sh
   git clone https://github.com/camel-ai/owl.git
   cd owl
   ```
#### 2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
#### 3. Set up environment variables:
   - Create a `.env` file and add your API keys/configuration as needed.

## Setup

#### 1. Install the required Node.js package:
   ```bash
   npm install -g @notionhq/notion-mcp-server@latest
   ```

#### 2. Set up your Notion integration:
   - Go to https://www.notion.so/profile/integrations
   - Create a new integration
   - Copy the integration token
   - Update `mcp_servers_config.json` with your token

#### 3. Connect your Notion pages:
   - Open each Notion page you want to work with
   - Click "..." (three dots) in the top right
   - Select "Add connections"
   - Choose your integration

#### 4. Visit official Notion MCP GitHub Repository
Visit the [Notion_MCP GitHub Repo](https://github.com/makenotion/notion-mcp-server) for detailed setup instructions.

## Usage

Navigate to the community use case directory before running the script:

```sh
cd community_usecase/Notion_MCP
```

#### Run the script using:
   ```bash
   python notion_manager.py
   ```
   This will run the default task which:
   - Searches for a specific page
   - Updates its properties
   - Adds a comment


## Supported Operations

The integration supports these Notion API operations:
- Searching for pages
- Reading page content
- Updating page properties
- Adding comments
- Creating new pages
- Retrieving database content

## Troubleshooting

If you encounter errors:

    1. Verify your Notion token is correct
    2. Check that pages are connected to your integration
    3. Ensure you have the required permissions
    4. Check the Notion API version in config matches the current version

## Error Handling

The script includes:
- Graceful connection handling
- Task execution error catching
- Proper cleanup on exit
- Windows-specific asyncio handling

## Repository

For more details, visit the OWL repository: [OWL GitHub Repo](https://github.com/camel-ai/owl)