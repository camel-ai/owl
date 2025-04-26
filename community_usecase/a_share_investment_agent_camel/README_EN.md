<h1 align="center">
	🦉A-Share Investment Agent System
</h1>



<div align="center">
<h4 align="center">
<div align="center">
A multi-agent A-share investment analysis system based on OWL/camel framework, implemented using the Camel framework.
</div>

[English](README_EN.md) |
[中文](README.md) |
[Acknowledgements](#-acknowledgements) |
[Example Results](#-example-results)

</h4>
</div>

<div align="center">
  <img src="screenshots/system_architecture.png" alt="System Architecture Diagram" width="700">
</div>

## 📋 Project Introduction

This project is a multi-agent A-share investment analysis system based on the OWL framework and Camel framework (v0.2.36), which completes investment analysis through multiple professional role agents working together to provide investment decision recommendations for users. The system adopts multi-model support and can flexibly use different large language models (such as Gemini, OpenAI, Qwen) for analysis.

This project participated in the OWL community use case challenge and is an improved version of the open-source project [A_Share_investment_Agent](https://github.com/24mlight/A_Share_investment_Agent), restructured using the OWL and Camel frameworks.

### 🌟 Core Features

- **Multi-agent Collaboration System**: Analysis through 10 professional role agents working together to achieve more comprehensive and professional investment decisions
- **Multi-model Support**: Support for multiple large language models such as Gemini, OpenAI, Qwen, with flexible switching
- **A-share Market Specialization**: Designed specifically for the A-share market, focusing on Chinese stock market characteristics and data
- **Debate and Decision Mechanism**: Innovative bull and bear perspective debate mechanism to balance analytical viewpoints
- **Complete Data Processing Pipeline**: Full process support from data collection to analysis to decision-making

## 🏗️ System Architecture

The system architecture includes the following core agents:

### 📊 Data and Analysis Layer
1. **Market Data Agent** - Responsible for collecting and preprocessing market data
2. **Technical Analyst** - Analyzes technical indicators and generates trading signals
3. **Fundamentals Analyst** - Analyzes fundamental data and generates trading signals
4. **Sentiment Analyst** - Analyzes market sentiment and generates trading signals
5. **Valuation Analyst** - Calculates the intrinsic value of stocks and generates trading signals

### 🔍 Research and Debate Layer
6. **Researcher Bull** - Provides bullish perspective analysis
7. **Researcher Bear** - Provides bearish perspective analysis
8. **Debate Room** - Integrates bull and bear perspectives to form a final viewpoint

### 🧮 Decision Layer
9. **Risk Manager** - Calculates risk indicators and sets position limits
10. **Portfolio Manager** - Formulates the final trading decision and generates orders

## 💻 Installation Guide

### Prerequisites

- Python 3.9+
- Related API keys (Gemini/OpenAI/Qwen)

### Installation Steps

1. Clone the OWL repository and enter the project directory
```bash
git clone https://github.com/camel-ai/owl.git
cd owl/community_usecase/a_share_investment_agent_camel
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure environment variables (create .env file)
```
# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o

# Qwen Configuration
QWEN_API_KEY=your_qwen_api_key
QWEN_MODEL=qwen-max
QWEN_API_URL=https://your-qwen-api-endpoint
```

### Docker Usage Method

To simplify the installation process, we provide Docker support.

1. Build Docker image
```bash
docker build -t a-share-investment-agent .
```

2. Create a .env file containing API keys
```bash
# Create a .env file with the same format as above
touch .env
# Edit the .env file to add your API keys
```

## 🚀 Usage

### Basic Usage

```bash
python src/main.py --ticker 000001 --model qwen
```

### Test Mode

```bash
# Use default parameters (Qwen model and 000001 stock) for testing
python src/main.py --test

# Specify stock for testing
python src/main.py --test --ticker 600036
```

### Parameter Description

- `--ticker`: Stock code
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--show-reasoning`: Display analysis reasoning process
- `--num-of-news`: Number of news used for sentiment analysis
- `--initial-capital`: Initial cash amount
- `--initial-position`: Initial stock position
- `--model`: Model to use (gemini, openai, qwen)
- `--test`: Run test function with preset parameters

## 🚀 Example Results

### Analysis Results

Below is an example of the analysis results for Cambricon-U (688256) stock during the period 2025/01/04-2025/03/24:

```bash
python src/main.py --ticker 688256 --start-date 2025-01-04 --end-date 2025-03-24 --model qwen --show-reasoning
```

#### Agent Analysis Logs

**Market Data Agent**:
```json
{
"trend": "Short-term trend is downward, but long-term trend still needs observation",
"judgment": "Current price is below the middle Bollinger band, RSI is close to neutral level, MACD line is below the signal line, indicating short-term adjustment may continue. However, considering the previous significant rise, the long-term trend still needs further observation. Recommend paying attention to support level 670.66 and resistance level 747.57."
}
```

**Technical Analyst**:
```json
{
  "signal": "bearish",
  "confidence": 0.8,
  "reasoning": "From technical indicators, the stock is currently in a relatively weak state. First, the 5-day moving average (718.856) has crossed below the 10-day (743.927) and 20-day (747.574) moving averages, indicating the short-term trend is weakening. The MACD indicator also shows a similar trend, with the MACD line (8.994) below the signal line (20.004), and the MACD histogram (-11.009) negative, indicating market momentum is weakening. The RSI indicator (48.676) is in neutral territory but approaching oversold territory, which may indicate a short-term rebound, but the overall trend remains weak. On the Bollinger Bands, the current price (685.05) is close to the lower band (670.657), which may provide some support, but considering the weakness shown by other indicators, the support may be limited. Overall, the current market environment and technical indicators point toward a bearish trend."
}
```

**Fundamentals Analyst**:
```json
{
  "signal": "bearish",
  "confidence": 0.8,
  "reasoning": "Cambricon-U's financial condition and business performance show clear negative trends. First, the company's net profit continues to be negative, and the loss amount has increased in recent quarters, indicating serious problems with profitability. Second, although the company's operating revenue increased in the fourth quarter of 2023, it experienced a significant decline in subsequent quarters, which may indicate a decrease in market demand or company market share. Additionally, the company's P/E ratio is negative, and its P/B ratio is as high as 52.58, indicating overvaluation in the market with significant bubble risk. From a financial health perspective, although the company has a low debt-to-asset ratio, its operating cash flow continues to be negative, indicating the company faces significant financial pressure in operations. Considering these factors, we believe Cambricon-U's stock is currently bearish."
}
```

**Sentiment Analyst**:
```json
{
  "signal": "bullish",
  "confidence": 0.8,
  "reasoning": "From the news data, the overall market sentiment is positive, with positive news far outnumbering negative news. Although one news item mentions the decline of chip ETFs and Cambricon-U, most news emphasizes the positive performance of Cambricon-U and its sector, including stock price increases and technological breakthroughs. Additionally, the news of Cambricon-U being included in the FTSE China A50 Index indicates the market's optimistic outlook for its long-term prospects. Social media discussions also mainly focus on the company's positive developments, further supporting the bullish view.",
  "key_events": [
    "Cambricon-U included in FTSE China A50 Index",
    "Cambricon-U stock price rises multiple times",
    "AI AIETF holding stock Cambricon-U surges",
    "ZhiYuan QiYuan large model released"
  ]
}
```

**Valuation Analyst**:
```json
{
  "signal": "bearish",
  "confidence": 0.85,
  "reasoning": "Cambricon-U's financial condition and business performance show clear negative trends. First, the company's net profit continues to be negative, and the loss amount has increased in recent quarters, indicating serious problems with profitability. Second, although the company's operating revenue increased in the fourth quarter of 2023, it experienced a significant decline in subsequent quarters, which may indicate a decrease in market demand or company market share. Additionally, the company's P/E ratio is negative, and its P/B ratio is as high as 52.58, indicating overvaluation in the market with significant bubble risk. From a financial health perspective, although the company has a low debt-to-asset ratio, its operating cash flow continues to be negative, indicating the company faces significant financial pressure in operations. Considering these factors, we believe Cambricon-U's stock is currently bearish. Furthermore, calculated through DCF model and relative valuation methods, the company's intrinsic value is significantly lower than the current market price, further supporting the bearish view.",
  "fair_value": 200.0,
  "key_metrics": [
    "P/E Ratio",
    "P/B Ratio",
    "Operating Revenue",
    "Net Profit",
    "Operating Cash Flow"
  ]
}
```

**Researcher Bull**:
```json
{
  "key_points": [
    "Market sentiment is positive, news and social media discussions lean optimistic",
    "Cambricon-U included in FTSE China A50 Index, indicating market's optimistic outlook for its long-term prospects",
    "Positive news of technological breakthroughs and stock price increases",
    "Despite weakness in technical and fundamental aspects, market sentiment and potential catalysts may drive stock price rebound"
  ],
  "confidence": 0.6,
  "reasoning": "Despite technical and fundamental analysis showing Cambricon-U is currently in a weak state, market sentiment and potential catalysts may drive stock price rebound. Cambricon-U being included in the FTSE China A50 Index indicates the market's optimistic outlook for its long-term prospects. Additionally, recent positive news about technological breakthroughs and stock price increases also support the bullish view. Although current financial conditions and valuations are high, market sentiment and potential positive factors may provide support for the stock price. Therefore, we recommend maintaining caution in the short term, but in the long term, Cambricon-U still has investment potential."
}
```

**Researcher Bear**:
```json
{
  "key_points": [
    "Technical indicators show short-term trend weakening",
    "Net profit continues to be negative and losses increase",
    "Declining operating revenue indicates decreased market demand",
    "P/B ratio as high as 52.58, overvalued",
    "Operating cash flow continues to be negative, significant financial pressure",
    "DCF model and relative valuation methods show intrinsic value lower than market price"
  ],
  "confidence": 0.8,
  "reasoning": "Combining technical analysis, fundamental analysis, market sentiment analysis, and valuation analysis, Cambricon-U's stock is currently bearish. Technical indicators show short-term trend weakening, fundamental analysis shows poor profitability, decreased market demand, overvaluation, and significant financial pressure. Although market sentiment leans positive, these positive sentiments mainly focus on short-term events and cannot mask long-term fundamental issues. Valuation analysis further supports the bearish view, with intrinsic value significantly lower than current market price. Therefore, selling Cambricon-U stock is recommended."
}
```

**Debate Room**:
```json
{
  "signal": "neutral",
  "confidence": 0.7,
  "reasoning": "Both bull and bear researchers' views have rationality and basis. The bull researcher emphasizes positive market sentiment, Cambricon-U's inclusion in the FTSE China A50 Index, and positive news about technological breakthroughs and stock price increases, which may provide support for the stock price in the short term. However, the bear researcher points out technical indicators show short-term trend weakening, fundamental analysis shows poor profitability, decreased market demand, overvaluation, and significant financial pressure. Although market sentiment leans positive, these positive sentiments mainly focus on short-term events and cannot mask long-term fundamental issues. Overall, in the short term, market sentiment and technological breakthroughs may drive stock price rebound, but long-term fundamental issues still exist, so maintaining a neutral attitude and waiting for more clear signals is recommended.",
  "final_verdict": "Investors are advised to remain cautious in the short term and pay attention to the continuity of market sentiment and technological breakthroughs. In the long term, close attention should be paid to the company's fundamental improvements, especially in areas such as profitability, market demand, and financial pressure. Before more clear signals emerge, maintaining a neutral attitude and avoiding excessive optimism or pessimism is recommended."
}
```

**Risk Manager**:
```json
{
  "max_position_size": 0.2,
  "volatility": 0.15,
  "risk_score": 0.7,
  "max_drawdown": 0.25,
  "suggested_position_size": 0.15,
  "reasoning": "Given stock 688256's high volatility and fundamental risks, a cautious approach is recommended. Although there is potential for technical breakthrough in the short term, the company faces issues such as poor profitability in the long term. Therefore, it is recommended to control position ratio not exceeding 20% and set appropriate stop-loss points to protect capital. At the same time, diversify investments to spread risk."
}
```

**Portfolio Manager (Final Decision)**:
```json
{
  "action": "hold",
  "quantity": 0,
  "confidence": 0.8,
  "reasoning": "Considering various analysts' trading signals, debate results, risk analysis, current portfolio status, and latest market price, we decide to adopt a holding strategy for stock 688256. Technical analysis and fundamental analysis both show the stock is in a weak state, with technical indicators showing short-term trend weakening, and fundamentals showing poor profitability, decreased market demand, overvaluation, and significant financial pressure. Although sentiment analysis shows positive market sentiment, these positive sentiments mainly focus on short-term events and cannot mask long-term fundamental issues. The debate result also recommends caution in the short term, paying attention to the continuity of market sentiment and technological breakthroughs. In the long term, close attention should be paid to the company's fundamental improvements. Risk analysis recommends controlling position ratio not exceeding 20% and setting appropriate stop-loss points to protect capital. Therefore, we decide to temporarily hold the stock and wait for more clear signals."
}
```

#### Comprehensive Conclusion

**Final Investment Decision**: Hold (Confidence: 0.8)

The analysis results from multiple professional agents indicate that Cambricon-U (688256) stock is currently in a weak state in terms of technicals and fundamentals, but market sentiment and short-term events may provide support for the stock price. Considering all factors, the system recommends adopting a holding strategy for this stock and closely monitoring subsequent changes in fundamentals and market sentiment. At the same time, risk management recommends controlling the maximum position ratio of this stock to within 20% of the portfolio and setting appropriate stop-loss points to control risk.

## 🔄 Data Process Description

The system's data process follows these steps:

1. **Data Collection**: Market data agent collects A-share market data and news through akshare API
2. **Multi-dimensional Analysis**: Four professional analysis agents (technical, fundamental, sentiment, valuation) conduct analysis independently
3. **Bull/Bear Research**: Bull and bear researchers provide analysis reports from bullish and bearish perspectives respectively
4. **Debate Integration**: Debate room integrates bull and bear perspectives to form a final analytical opinion
5. **Risk Assessment**: Risk manager assesses investment risk and sets trading restrictions
6. **Final Decision**: Portfolio manager formulates the final trading decision and generates orders


## 📋 Project Structure

```
community_usecase/a_share_investment_agent_camel/
├── src/                       # Source code directory
│   ├── agents/                # Agent implementations
│   │   ├── base_agent.py      # Base agent class
│   │   ├── market_data_agent.py  # Market data agent
│   │   ├── technical_analyst.py  # Technical analyst agent
│   │   └── ...
│   ├── tools/                 # Tool modules
│   │   └── data_helper.py     # Data helper tools
│   ├── utils/                 # Utility tools
│   │   └── logging_utils.py   # Logging tools
│   ├── models.py              # Data model definitions
│   ├── roles.py               # Role definitions
│   └── main.py                # Main program
├── tests/                     # Test directory
├── logs/                      # Log files
├── .env                       # Environment variables
├── pyproject.toml             # Poetry configuration
├── requirements.txt           # Dependencies
└── README.md                  # Documentation
```

## 🔍 Code Implementation Highlights

### 1. Multi-agent Collaboration Architecture

This project implements 10 professional role agents, with each agent responsible for specific tasks in the investment analysis process. Agents collaborate through message passing, forming a complete analysis decision chain.

```python
# Create agents
market_data_agent = MarketDataAgent(show_reasoning=show_reasoning, model_name=model_name)
technical_analyst = TechnicalAnalystAgent(show_reasoning=show_reasoning, model_name=model_name)
fundamentals_analyst = FundamentalsAnalystAgent(show_reasoning=show_reasoning, model_name=model_name)
sentiment_analyst = SentimentAnalystAgent(show_reasoning=show_reasoning, model_name=model_name)
valuation_analyst = ValuationAnalystAgent(show_reasoning=show_reasoning, model_name=model_name)
researcher_bull = ResearcherBullAgent(show_reasoning=show_reasoning, model_name=model_name)
researcher_bear = ResearcherBearAgent(show_reasoning=show_reasoning, model_name=model_name)
debate_room = DebateRoomAgent(show_reasoning=show_reasoning, model_name=model_name)
risk_manager = RiskManagerAgent(show_reasoning=show_reasoning, model_name=model_name)
portfolio_manager = PortfolioManagerAgent(show_reasoning=show_reasoning, model_name=model_name)
```

### 2. Flexible Multi-model Support

The system supports multiple large language models including Gemini, OpenAI, and Qwen, implementing flexible switching through a unified interface.

```python
def get_llm_client(model_name: str):
    """Get the specified LLM client"""
    if model_name.lower() == 'gemini':
        return GeminiClient()
    elif model_name.lower() == 'openai':
        return OpenAIClient()
    elif model_name.lower() == 'qwen':
        return QwenClient()
    else:
        raise ValueError(f"Unsupported model: {model_name}")
```



## 📝 Improvements and Innovations

Compared to the original version, the system restructured based on the Camel framework has the following innovations and improvements:

1. **Modular Design**: Clearer agent definitions and system structure, facilitating extension and maintenance
2. **Multi-model Support**: Flexible support for multiple LLM models, improving system adaptability
3. **Comprehensive Logging System**: Detailed recording of each agent's work process, facilitating debugging and analysis


## ⚠️ Disclaimer

This project is for **educational and research purposes only**.

- Not suitable for actual trading or investment
- No guarantees provided
- Past performance does not represent future performance
- Creators bear no responsibility for any financial losses
- Consult professional financial advisors for investment decisions

By using this software, you agree to use it for learning purposes only.

## 📚 Related Resources

- [OWL Framework Official Documentation](https://github.com/camel-ai/owl)
- [Camel Framework Official Documentation](https://github.com/camel-ai/camel)
- [A_Share_investment_Agent](https://github.com/24mlight/A_Share_investment_Agent)

## 🙏 Acknowledgements

This project is improved based on the following open-source projects:

1. [A_Share_investment_Agent](https://github.com/24mlight/A_Share_investment_Agent) - Original A-share investment agent project, providing the foundation architecture and investment analysis ideas for this project. Special thanks for its innovative design in A-share data processing and analysis strategies.
2. [ai-hedge-fund](https://github.com/virattt/ai-hedge-fund.git) - Original US stock investment agent project
3. [Camel Framework](https://github.com/camel-ai/camel) - Multi-agent dialogue framework
4. [OWL Framework](https://github.com/camel-ai/owl) - Open-source multi-agent collaboration framework

Thanks to all the original authors for their contributions and inspiration, providing a solid foundation for this project. 