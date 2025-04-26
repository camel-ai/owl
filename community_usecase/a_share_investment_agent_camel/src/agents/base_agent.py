"""
代理基类模块

定义所有代理的共同基类和接口
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import json
import logging
import re
from camel.agents import ChatAgent
from camel.messages import BaseMessage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/agents.log"),
        logging.StreamHandler()
    ]
)


class BaseAgent(ABC):
    """代理基类"""
    
    def __init__(self, role_agent: ChatAgent, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化代理
        
        Args:
            role_agent: Camel框架的聊天代理
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        self.agent = role_agent
        self.show_reasoning = show_reasoning
        self.model_name = model_name
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def log_message(self, message: BaseMessage) -> None:
        """记录消息
        
        Args:
            message: 要记录的消息
        """
        if self.show_reasoning:
            print(f"\n{'='*80}")
            print(f"【{self.__class__.__name__}】推理过程:")
            print(f"{'-'*80}")
            print(message.content)
            print(f"{'='*80}\n")
        
        # 记录到日志
        self.logger.info(f"推理过程: {message.content[:100]}...")
        
    def format_data(self, data: Dict[str, Any]) -> str:
        """格式化数据为字符串
        
        Args:
            data: 要格式化的数据
            
        Returns:
            str: 格式化后的字符串
        """
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """从响应中解析JSON
        
        尝试从响应文本中提取JSON数据，处理各种边缘情况
        
        Args:
            response: 响应文本
            
        Returns:
            Dict[str, Any]: 解析后的JSON数据
        """
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 尝试从Markdown代码块中提取JSON
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(json_pattern, response)
        
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # 尝试找到大括号包裹的内容
        brace_pattern = r"\{[\s\S]*\}"
        matches = re.findall(brace_pattern, response)
        
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # 如果所有尝试都失败，返回空字典并记录错误
        self.logger.error(f"无法从响应中解析JSON: {response}")
        return {}
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据并返回结果
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        pass 

    def generate_human_message(self, content: str) -> BaseMessage:
        """生成人类消息
        
        Args:
            content: 消息内容
            
        Returns:
            BaseMessage: 用户消息对象
        """
        return BaseMessage.make_user_message(role_name="user", content=content)
        
    def generate_ai_message(self, content: str) -> BaseMessage:
        """生成AI消息
        
        Args:
            content: 消息内容
            
        Returns:
            BaseMessage: 助手消息对象
        """
        return BaseMessage.make_assistant_message(role_name="assistant", content=content) 