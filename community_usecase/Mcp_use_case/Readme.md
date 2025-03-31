# Content Curation with OWL & MCP

This project leverages **OWL (Optimized Workforce Learning)** and **MCP (Multi-Agent Content Processing)** to automate content curation. The system scrapes top tech news websites, extracts relevant information, and compiles a summary report.

## Features

- Uses **MCPToolkit** for managing toolkits and performing web scraping.
- Implements **OwlRolePlaying** for enhanced multi-agent task execution.
- Scrapes **TechCrunch, The Verge, and Wired**.
- Extracts and summarizes **headlines, article summaries, and publication dates**.
- Generates a digest report **(Latest_tech_digest.md)** based on trends from these sources.

## Installation

1. Clone this repository:
   ```sh
   git clone https://github.com/your-repo.git
   cd your-repo
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file and add your API keys/configuration as needed.

## Usage

Run the script using:

```sh
python script.py "Your Custom Task Here"
```

Or use the default task defined in the script.

## Configuration

- The script reads from `mcp_servers_config.json` to configure MCP.
- Modify the `default_task` section to adjust scraping and summarization behavior.

## Error Handling

- The script ensures **graceful cleanup** in case of failures.
- Implements **try-except** blocks to handle tool execution errors.

## Cleanup & Shutdown

- The script **automatically disconnects MCP** after execution.
- Cancels running async tasks to **prevent memory leaks**.
- Handles **KeyboardInterrupt** for a graceful shutdown.

## Future Improvements

- Add support for more tech news sources.
- Implement NLP-based **sentiment analysis** on extracted news.
- Enable storing summaries in structured formats like JSON/CSV.


