"""
日志工具模块
"""
import logging
import os
from datetime import datetime
from typing import Optional


def setup_logger(name: str, log_level: int = logging.INFO, log_dir: str = "logs") -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别
        log_dir: 日志目录
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 获取日志记录器
    logger = logging.getLogger(name)
    
    # 如果已配置，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    logger.setLevel(log_level)
    
    # 创建文件处理器
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/{name}_{timestamp}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 设置格式化器
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


class OutputLogger:
    """
    输出日志记录器，用于重定向标准输出
    """
    def __init__(self, filename: Optional[str] = None):
        """
        初始化输出日志记录器
        
        Args:
            filename: 日志文件名，默认为自动生成
        """
        # 确保日志目录存在
        os.makedirs("logs", exist_ok=True)
        
        # 设置日志文件
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/output_{timestamp}.log"
        
        self.terminal = open(filename, "a", encoding="utf-8")
        self.terminal.write(f"=== 日志开始于 {datetime.now()} ===\n")
        self.stdout = None
    
    def write(self, message):
        """写入消息到终端和日志文件"""
        if self.stdout:
            self.stdout.write(message)
        self.terminal.write(message)
        self.terminal.flush()
    
    def flush(self):
        """刷新日志"""
        if self.stdout:
            self.stdout.flush()
        self.terminal.flush()
    
    def close(self):
        """关闭日志文件"""
        self.terminal.write(f"=== 日志结束于 {datetime.now()} ===\n")
        self.terminal.close()
    
    def __del__(self):
        """析构函数，确保关闭日志文件"""
        try:
            self.close()
        except:
            pass 