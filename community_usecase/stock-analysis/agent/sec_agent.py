
import os
from camel.agents.chat_agent import ChatAgent
from pydantic import BaseModel
from typing import List
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from tools.sec_tools import SECToolkit
from camel.toolkits import FunctionTool
from prompts import  get_sec_system_prompt

def create_sec_agent() -> ChatAgent:
    # Define the model, here in this case we use gpt-4o-mini
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
        model_type="glm-4-flash",
        api_key=os.getenv("ZHIPUAI_API_KEY"),
        url=os.getenv("ZHIPUAI_API_BASE_URL"),
        model_config_dict={"temperature": 0},
    )
    # Create agent with structured output
    agent = ChatAgent(
    system_message=get_sec_system_prompt(),
    model=model,
    tools = [
        *SECToolkit().get_tools()
    ]
    )
    return agent

def get_sec_summary_for_company(company_stock_name: str) -> str:
    r"""Retrieve and analyze SEC filing information for a specified company and generate a comprehensive analysis report.

    This function retrieves relevant documents from the SEC database using the company's stock symbol,
    analyzes key financial metrics, business developments, risk conditions, market position,
    and generates a structured analysis report.

    Args:
        company_stock_name (str): Company stock symbol (e.g., 'AAPL' for Apple Inc.)

    Returns:
        str: A comprehensive analysis report containing:
            - Key financial metrics from quarterly and annual reports
            - Important business developments, risks, and market position
            - Management discussion and strategic plans
            - Material changes in operations and financial conditions
            - Important regulatory disclosures and compliance matters
            
            The report is formatted as structured text, limited to 10,000 words,
            highlighting information most relevant and impactful to investors.
    """

    # Define Summary Prompt
    usr_msg = f"""Please search and analyze the SEC filings for {company_stock_name} and provide a comprehensive summary report. The report should:

1. Include key financial metrics and performance indicators from recent quarterly and annual reports
2. Highlight significant business developments, risks, and market position
3. Analyze management's discussion and strategic initiatives
4. Note any material changes in operations or financial condition
5. Summarize important regulatory disclosures and compliance matters

Please structure the analysis in a clear, concise manner and limit the total response to no more than 10,000 words. Focus on the most relevant and impactful information for investors."""

    # Sending the message to the agent
    agent = create_sec_agent()
    response = agent.step(usr_msg)

    # Check the response (just for illustrative purpose)
    # print(agent.memory.get_context())
    return response.msgs[0].content

get_sec_summary_for_company_tool = FunctionTool(get_sec_summary_for_company)

if __name__ == "__main__":
    get_sec_summary_for_company("GOOG")