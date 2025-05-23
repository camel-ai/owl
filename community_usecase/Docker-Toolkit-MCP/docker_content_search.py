import asyncio
import sys
import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.toolkits import FunctionTool, MCPToolkit, SearchToolkit
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level

from owl.utils.enhanced_role_playing import OwlRolePlaying, arun_society

set_log_level(level="DEBUG")
load_dotenv()

async def construct_society(
    question: str,
    tools: List[FunctionTool],
) -> OwlRolePlaying:
    """Construct OwlRolePlaying instance to enhance content search capabilities"""
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.DEEPSEEK,
            model_type=ModelType.DEEPSEEK_CHAT,
            model_config_dict={"temperature": 0.7},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.DEEPSEEK,
            model_type=ModelType.DEEPSEEK_CHAT,
            model_config_dict={"temperature": 0.7},
        ),
    }

    user_agent_kwargs = {
        "model": models["user"],
    }
    
    assistant_agent_kwargs = {
        "model": models["assistant"],
        "tools": tools,
    }

    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    return OwlRolePlaying(
        **task_kwargs,
        user_role_name="docker_content_curator",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="docker_tech_expert",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

async def save_search_results(content: str, token_count: int = None) -> Path:
    """Save search results as Markdown file
    
    Args:
        content: Search result content
        token_count: Number of tokens used
    
    Returns:
        Path to saved file
    """
    # Create output directory
    output_dir = Path(__file__).parent / "search_results"
    output_dir.mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"docker_toolkit_search_{timestamp}.md"
    output_path = output_dir / filename
    
    # Organize file content
    file_content = [
        "# Docker Toolkit Search Results",
        f"\n> Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    
    if token_count:
        file_content.append(f"\n> Tokens used: {token_count}")
        
    file_content.append("\n## Search Content\n")
    file_content.append(content)
    
    # Write to file
    output_path.write_text("\n".join(file_content), encoding="utf-8")
    
    return output_path

async def main():
    # Configure MCP toolkit and search toolkit
    config_path = Path(__file__).parent / "mcp_servers_config.json"
    mcp_toolkit = MCPToolkit(config_path=str(config_path))
    try:
        await mcp_toolkit.connect()

        default_task = (
            "Please help me search for Docker Toolkit related content:\n"
            "1. Docker Toolkit technical documentation and official guides\n"
            "2. Docker Toolkit video tutorials and practical cases\n"
            "3. Docker Toolkit best practices in development and operations\n"
            "4. Docker Toolkit performance optimization and troubleshooting guides\n"
            "\n"
            "Please note:\n"
            "- Prioritize recent content\n"
            "- Ensure content quality and reliability\n"
            "- Include both English and Chinese resources\n"
            "- Focus on practical experience and case studies\n"
            "\n"
            "Please organize in the following format:\n"
            "## Documentation and Guides\n"
            "- [Title](link)\n"
            "  Brief description\n"
            "\n"
            "## Video Tutorials\n"
            "- [Title](link)\n"
            "  Duration | Author | Brief description\n"
            "\n"
            "## Best Practices\n"
            "- [Title](link)\n"
            "  Brief description\n"
            "\n"
            "## Troubleshooting and Optimization\n"
            "- [Title](link)\n"
            "  Brief description"
        )

        task = sys.argv[1] if len(sys.argv) > 1 else default_task

        # Combine MCP tools and search tools
        tools = [
            *mcp_toolkit.get_tools(),
        ]
        
        society = await construct_society(task, tools)
        
        try:
            result = await arun_society(society)
            
            if isinstance(result, tuple) and len(result) == 3:
                answer, chat_history, token_count = result
                print("\n🔍 Search Results:")
                print("=" * 80)
                print(answer)
                print("=" * 80)
                print(f"\n📊 Tokens used: {token_count}")
                
                # Save search results
                output_path = await save_search_results(answer, token_count)
                print(f"\n💾 Results saved to: {output_path}")
                
            else:
                print("\n🔍 Search Results:")
                print("=" * 80)
                print(str(result))
                print("=" * 80)
                
                # Save search results
                output_path = await save_search_results(str(result))
                print(f"\n💾 Results saved to: {output_path}")

        except Exception as e:
            print(f"❌ Search execution error: {str(e)}")
            raise

    finally:
        try:
            await mcp_toolkit.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
