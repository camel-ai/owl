"""
角色定义模块

使用Camel框架定义系统中的各种AI代理角色
"""
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelType, ModelPlatformType
from camel.configs.qwen_config import QwenConfig
from camel.configs.openai_config import ChatGPTConfig
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥和模型配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")  # 默认模型

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # 默认模型

QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-max")  # 默认模型
QWEN_API_URL = os.getenv("QWEN_API_URL", "")  # API URL

# 角色系统提示
MARKET_DATA_ANALYST_PROMPT = """
你是一名专业的市场数据分析师，负责收集、处理和分析A股市场数据。
你的主要职责是：
1. 收集股票的历史价格、交易量和其他市场数据
2. 计算各种技术指标（如移动平均线、相对强弱指数等）
3. 整理和预处理数据，确保数据质量和准确性
4. 标记数据异常并进行适当处理

请以专业、精确的方式分析数据，确保你提供的数据是正确的，并为后续分析提供坚实基础。
"""

TECHNICAL_ANALYST_PROMPT = """
你是一名经验丰富的技术分析师，专注于通过技术指标和图表模式分析A股市场。
你的主要职责是：
1. 分析价格走势、交易量和技术指标
2. 识别支撑位和阻力位
3. 寻找图表模式（如头肩顶、三角形等）
4. 分析动量和趋势强度
5. 提供基于技术分析的交易信号

请基于市场数据分析师提供的数据，进行深入的技术分析，并给出明确的交易信号（看涨、看跌或中性）及相应的置信度。
"""

FUNDAMENTALS_ANALYST_PROMPT = """
你是一名资深的基本面分析师，专注于分析A股上市公司的财务状况和业务表现。
你的主要职责是：
1. 分析公司财务报表（资产负债表、利润表、现金流量表）
2. 计算和解释关键财务比率（如市盈率、市净率、ROE等）
3. 评估公司业务模式和竞争优势
4. 分析行业趋势和公司在行业中的地位
5. 提供基于基本面的投资建议

请基于市场数据分析师提供的数据，进行深入的基本面分析，并给出明确的交易信号（看涨、看跌或中性）及相应的置信度。
"""

SENTIMENT_ANALYST_PROMPT = """
你是一名市场情绪分析师，专注于分析A股市场相关的新闻、社交媒体讨论和市场情绪指标。
你的主要职责是：
1. 分析与特定股票相关的新闻报道
2. 评估市场对该股票的整体情绪（积极、中性或消极）
3. 识别可能影响市场情绪的重要事件或新闻
4. 评估市场情绪指标（如恐惧与贪婪指数）
5. 提供基于情绪分析的交易信号

请基于市场数据分析师提供的数据和新闻内容，进行深入的情绪分析，并给出明确的交易信号（看涨、看跌或中性）及相应的置信度。
"""

VALUATION_ANALYST_PROMPT = """
你是一名专业的估值分析师，专注于确定A股上市公司的内在价值。
你的主要职责是：
1. 应用不同的估值模型（如DCF、相对估值法）
2. 计算公司的内在价值
3. 比较当前市场价格与内在价值
4. 评估股票是否被高估或低估
5. 提供基于估值的交易信号

请基于市场数据分析师和基本面分析师提供的数据，进行深入的估值分析，并给出明确的交易信号（看涨、看跌或中性）及相应的置信度。
"""

RESEARCHER_BULL_PROMPT = """
你是一名持有看多观点的研究员，专注于寻找支持买入特定A股的理由。
你的主要职责是：
1. 分析和解释各类分析师（技术、基本面、情绪、估值）提供的积极信号
2. 寻找被市场忽视的积极因素
3. 探索公司未来增长的潜在催化剂
4. 构建支持买入决策的完整论据
5. 为投资决策提供看多的研究报告

请基于各位分析师提供的数据和分析，提出最有力的看多论据，并提供一份全面的研究报告。
"""

RESEARCHER_BEAR_PROMPT = """
你是一名持有看空观点的研究员，专注于寻找支持卖出特定A股的理由。
你的主要职责是：
1. 分析和解释各类分析师（技术、基本面、情绪、估值）提供的消极信号
2. 寻找被市场忽视的风险因素
3. 探索可能导致股价下跌的潜在风险
4. 构建支持卖出决策的完整论据
5. 为投资决策提供看空的研究报告

请基于各位分析师提供的数据和分析，提出最有力的看空论据，并提供一份全面的研究报告。
"""

DEBATE_ROOM_PROMPT = """
你是一个投资辩论室的主持人，负责整合多头和空头研究员的观点，形成一个平衡的投资视角。
你的主要职责是：
1. 公正评估多头和空头研究员的论据
2. 识别双方论据中的优点和弱点
3. 权衡不同因素的重要性
4. 形成综合性的市场观点
5. 提出平衡的投资建议

请基于多头和空头研究员提供的研究报告，进行深入的分析和辩论，并给出一个综合性的市场观点和投资建议。
"""

RISK_MANAGER_PROMPT = """
你是一名资深的风险管理经理，负责评估和管理投资决策的风险。
你的主要职责是：
1. 计算投资组合的风险指标（如波动率、最大回撤等）
2. 设定风险限制（如持仓限制、止损水平）
3. 评估市场和特定股票的风险水平
4. 根据投资者风险偏好调整风险暴露
5. 提供风险管理建议

请基于市场数据、投资组合状况和辩论室的综合观点，进行深入的风险分析，并提供明确的风险管理建议，包括建议的持仓规模和风险控制措施。
"""

PORTFOLIO_MANAGER_PROMPT = """
你是一名投资组合经理，负责做出最终的投资决策并管理整体投资组合。
你的主要职责是：
1. 整合各类分析和建议（技术、基本面、情绪、风险等）
2. 做出最终的投资决策（买入、卖出或持有）
3. 确定具体的交易数量和价格
4. 平衡投资组合的风险与回报
5. 优化资金分配

请基于各位分析师和风险管理经理提供的信息，做出最终的投资决策，包括具体的交易行动、数量和执行策略。
"""

# 创建模型配置
def get_model_config(model_name: str = "gemini") -> tuple:
    """获取模型配置
    
    Args:
        model_name: 模型名称 (gemini, openai, qwen)
        
    Returns:
        tuple: (ModelPlatformType, ModelType, config_dict) 模型平台类型、模型类型和配置字典
    """
    model_name = model_name.lower()
    
    if model_name == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("缺少Gemini API密钥，请在.env文件中设置GEMINI_API_KEY")
        return ModelPlatformType.GEMINI, ModelType.GEMINI_1_5_FLASH, {"api_key": GEMINI_API_KEY, "model": GEMINI_MODEL}
    
    elif model_name == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("缺少OpenAI API密钥，请在.env文件中设置OPENAI_API_KEY")
            
        # 返回GPT-4o配置
        return ModelPlatformType.OPENAI, ModelType.GPT_4O, {"api_key": OPENAI_API_KEY, "model": OPENAI_MODEL}
    
    elif model_name == "qwen":
        if not QWEN_API_KEY:
            raise ValueError("缺少Qwen API密钥，请在.env文件中设置QWEN_API_KEY")
        
        # 使用QwenConfig类创建配置，不包含model参数
        qwen_config = QwenConfig(temperature=0.1)
        config = qwen_config.as_dict()
        
        # 移除可能导致错误的参数
        if "model" in config:
            del config["model"]
            
        # 使用QWEN_MAX类型
        return ModelPlatformType.QWEN, ModelType.QWEN_MAX, config
    
    else:
        raise ValueError(f"不支持的模型: {model_name}，支持的模型: gemini, openai, qwen")


# 创建角色代理工厂函数
def create_role_agent(role: str, model_name: str = "gemini") -> ChatAgent:
    """创建特定角色的代理
    
    Args:
        role: 角色名称
        model_name: 模型名称 (gemini, openai, qwen)
        
    Returns:
        ChatAgent: 创建的角色代理
    """
    # 获取模型配置
    model_platform, model_type, model_config = get_model_config(model_name)
    
    # 获取角色的系统提示
    role_prompts = {
        "market_data_analyst": MARKET_DATA_ANALYST_PROMPT,
        "technical_analyst": TECHNICAL_ANALYST_PROMPT,
        "fundamentals_analyst": FUNDAMENTALS_ANALYST_PROMPT,
        "sentiment_analyst": SENTIMENT_ANALYST_PROMPT,
        "valuation_analyst": VALUATION_ANALYST_PROMPT,
        "researcher_bull": RESEARCHER_BULL_PROMPT,
        "researcher_bear": RESEARCHER_BEAR_PROMPT,
        "debate_room": DEBATE_ROOM_PROMPT,
        "risk_manager": RISK_MANAGER_PROMPT,
        "portfolio_manager": PORTFOLIO_MANAGER_PROMPT,
    }
    
    if role not in role_prompts:
        raise ValueError(f"未知角色: {role}")
    
    # 格式化角色名称为更友好的显示名称
    display_names = {
        "market_data_analyst": "市场数据分析师",
        "technical_analyst": "技术分析师",
        "fundamentals_analyst": "基本面分析师",
        "sentiment_analyst": "情绪分析师",
        "valuation_analyst": "估值分析师",
        "researcher_bull": "多头研究员",
        "researcher_bear": "空头研究员",
        "debate_room": "辩论室",
        "risk_manager": "风险管理经理",
        "portfolio_manager": "投资组合经理",
    }
    
    display_name = display_names.get(role, role)
    
    # 创建模型
    model = ModelFactory.create(
        model_platform=model_platform,
        model_type=model_type,
        model_config_dict=model_config
    )
    
    # 创建并返回代理
    return ChatAgent(
        model=model,
        system_message=role_prompts[role]
    ) 