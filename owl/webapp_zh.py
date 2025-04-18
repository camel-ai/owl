# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Import from the correct module path
from utils import run_society
import os
import gradio as gr
import time
import json
import logging
import datetime
from typing import Tuple
import importlib
from dotenv import load_dotenv, set_key, find_dotenv, unset_key
import threading
import queue
import re  # For regular expression operations

os.environ["PYTHONIOENCODING"] = "utf-8"


# 配置日志系统
def setup_logging():
    """配置日志系统，将日志输出到文件和内存队列以及控制台"""
    # 创建logs目录（如果不存在）
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # 生成日志文件名（使用当前日期）
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"gradio_log_{current_date}.txt")

    # 配置根日志记录器（捕获所有日志）
    root_logger = logging.getLogger()

    # 清除现有的处理器，避免重复日志
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(logging.INFO)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.INFO)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到根日志记录器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("日志系统已初始化，日志文件: %s", log_file)
    return log_file


# 全局变量
LOG_FILE = None
LOG_QUEUE: queue.Queue = queue.Queue()  # 日志队列
STOP_LOG_THREAD = threading.Event()
CURRENT_PROCESS = None  # 用于跟踪当前运行的进程
STOP_REQUESTED = threading.Event()  # 用于标记是否请求停止


# 日志读取和更新函数
def log_reader_thread(log_file):
    """后台线程，持续读取日志文件并将新行添加到队列中"""
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # 移动到文件末尾
            f.seek(0, 2)

            while not STOP_LOG_THREAD.is_set():
                line = f.readline()
                if line:
                    LOG_QUEUE.put(line)  # 添加到对话记录队列
                else:
                    # 没有新行，等待一小段时间
                    time.sleep(0.1)
    except Exception as e:
        logging.error(f"日志读取线程出错: {str(e)}")


def get_latest_logs(max_lines=100, queue_source=None):
    """从队列中获取最新的日志行，如果队列为空则直接从文件读取

    Args:
        max_lines: 最大返回行数
        queue_source: 指定使用哪个队列，默认为LOG_QUEUE

    Returns:
        str: 日志内容
    """
    logs = []
    log_queue = queue_source if queue_source else LOG_QUEUE

    # 创建一个临时队列来存储日志，以便我们可以处理它们而不会从原始队列中删除它们
    temp_queue = queue.Queue()
    temp_logs = []

    try:
        # 尝试从队列中获取所有可用的日志行
        while not log_queue.empty() and len(temp_logs) < max_lines:
            log = log_queue.get_nowait()
            temp_logs.append(log)
            temp_queue.put(log)  # 将日志放回临时队列
    except queue.Empty:
        pass

    # 处理对话记录
    logs = temp_logs

    # 如果没有新日志或日志不足，尝试直接从文件读取最后几行
    if len(logs) < max_lines and LOG_FILE and os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                # 如果队列中已有一些日志，只读取剩余需要的行数
                remaining_lines = max_lines - len(logs)
                file_logs = (
                    all_lines[-remaining_lines:]
                    if len(all_lines) > remaining_lines
                    else all_lines
                )

                # 将文件日志添加到队列日志之前
                logs = file_logs + logs
        except Exception as e:
            error_msg = f"读取日志文件出错: {str(e)}"
            logging.error(error_msg)
            if not logs:  # 只有在没有任何日志的情况下才添加错误消息
                logs = [error_msg]

    # 如果仍然没有日志，返回提示信息
    if not logs:
        return "初始化运行中..."

    # 过滤日志，只保留 camel.agents.chat_agent - INFO 的日志
    filtered_logs = []
    for log in logs:
        if "camel.agents.chat_agent - INFO" in log:
            filtered_logs.append(log)

    # 如果过滤后没有日志，返回提示信息
    if not filtered_logs:
        return "暂无对话记录。"

    # 处理日志内容，提取最新的用户和助手消息
    simplified_logs = []

    # 使用集合来跟踪已经处理过的消息，避免重复
    processed_messages = set()

    def process_message(role, content):
        # 创建一个唯一标识符来跟踪消息
        msg_id = f"{role}:{content}"
        if msg_id in processed_messages:
            return None

        processed_messages.add(msg_id)
        content = content.replace("\\n", "\n")
        lines = [line.strip() for line in content.split("\n")]
        content = "\n".join(lines)

        role_emoji = "🙋" if role.lower() == "user" else "🤖"
        return f"""### {role_emoji} {role.title()} Agent

{content}"""

    for log in filtered_logs:
        formatted_messages = []
        # 尝试提取消息数组
        messages_match = re.search(
            r"Model (.*?), index (\d+), processed these messages: (\[.*\])", log
        )

        if messages_match:
            try:
                messages = json.loads(messages_match.group(3))
                for msg in messages:
                    if msg.get("role") in ["user", "assistant"]:
                        formatted_msg = process_message(
                            msg.get("role"), msg.get("content", "")
                        )
                        if formatted_msg:
                            formatted_messages.append(formatted_msg)
            except json.JSONDecodeError:
                pass

        # 如果JSON解析失败或没有找到消息数组，尝试直接提取对话内容
        if not formatted_messages:
            user_pattern = re.compile(r"\{'role': 'user', 'content': '(.*?)'\}")
            assistant_pattern = re.compile(
                r"\{'role': 'assistant', 'content': '(.*?)'\}"
            )

            for content in user_pattern.findall(log):
                formatted_msg = process_message("user", content)
                if formatted_msg:
                    formatted_messages.append(formatted_msg)

            for content in assistant_pattern.findall(log):
                formatted_msg = process_message("assistant", content)
                if formatted_msg:
                    formatted_messages.append(formatted_msg)

        if formatted_messages:
            simplified_logs.append("\n\n".join(formatted_messages))

    # 格式化日志输出，确保每个对话记录之间有适当的分隔
    formatted_logs = []
    for i, log in enumerate(simplified_logs):
        # 移除开头和结尾的多余空白字符
        log = log.strip()

        formatted_logs.append(log)

        # 确保每个对话记录以换行符结束
        if not log.endswith("\n"):
            formatted_logs.append("\n")

    return "\n".join(formatted_logs)


# Dictionary containing module descriptions
MODULE_DESCRIPTIONS = {
    "run": "默认模式：使用OpenAI模型的默认的智能体协作模式，适合大多数任务。",
    "run_mini": "使用使用OpenAI模型最小化配置处理任务",
    "run_gemini": "使用 Gemini模型处理任务",
    "run_deepseek_zh": "使用eepseek模型处理中文任务",
    "run_openai_compatible_model": "使用openai兼容模型处理任务",
    "run_ollama": "使用本地ollama模型处理任务",
    "run_qwen_mini_zh": "使用qwen模型最小化配置处理任务",
    "run_qwen_zh": "使用qwen模型处理任务",
    "run_azure_openai": "使用azure openai模型处理任务",
    "run_groq": "使用groq模型处理任务",
    "run_ppio": "使用ppio模型处理任务",
    "run_together_ai": "使用together ai模型处理任务",
}


# 默认环境变量模板
DEFAULT_ENV_TEMPLATE = """#===========================================
# MODEL & API 
# (See https://docs.camel-ai.org/key_modules/models.html#)
#===========================================

# OPENAI API (https://platform.openai.com/api-keys)
OPENAI_API_KEY='Your_Key'
# OPENAI_API_BASE_URL=""

# Azure OpenAI API
# AZURE_OPENAI_BASE_URL=""
# AZURE_API_VERSION=""
# AZURE_OPENAI_API_KEY=""
# AZURE_DEPLOYMENT_NAME=""


# Qwen API (https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key)
QWEN_API_KEY='Your_Key'

# DeepSeek API (https://platform.deepseek.com/api_keys)
DEEPSEEK_API_KEY='Your_Key'

#===========================================
# Tools & Services API
#===========================================

# Google Search API (https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3)
GOOGLE_API_KEY='Your_Key'
SEARCH_ENGINE_ID='Your_ID'

# Chunkr API (https://chunkr.ai/)
CHUNKR_API_KEY='Your_Key'

# Firecrawl API (https://www.firecrawl.dev/)
FIRECRAWL_API_KEY='Your_Key'
#FIRECRAWL_API_URL="https://api.firecrawl.dev"
"""


def validate_input(question: str) -> bool:
    """验证用户输入是否有效

    Args:
        question: 用户问题

    Returns:
        bool: 输入是否有效
    """
    # 检查输入是否为空或只包含空格
    if not question or question.strip() == "":
        return False
    return True


def run_owl(question: str, example_module: str) -> Tuple[str, str, str]:
    """运行OWL系统并返回结果

    Args:
        question: 用户问题
        example_module: 要导入的示例模块名（如 "run_terminal_zh" 或 "run_deep"）

    Returns:
        Tuple[...]: 回答、令牌计数、状态
    """
    global CURRENT_PROCESS

    # 验证输入
    if not validate_input(question):
        logging.warning("用户提交了无效的输入")
        return ("请输入有效的问题", "0", "❌ 错误: 输入问题无效")

    try:
        # 确保环境变量已加载
        load_dotenv(find_dotenv(), override=True)
        logging.info(f"处理问题: '{question}', 使用模块: {example_module}")

        # 检查模块是否在MODULE_DESCRIPTIONS中
        if example_module not in MODULE_DESCRIPTIONS:
            logging.error(f"用户选择了不支持的模块: {example_module}")
            return (
                f"所选模块 '{example_module}' 不受支持",
                "0",
                "❌ 错误: 不支持的模块",
            )

        # 动态导入目标模块
        module_path = f"examples.{example_module}"
        try:
            logging.info(f"正在导入模块: {module_path}")
            module = importlib.import_module(module_path)
        except ImportError as ie:
            logging.error(f"无法导入模块 {module_path}: {str(ie)}")
            return (
                f"无法导入模块: {module_path}",
                "0",
                f"❌ 错误: 模块 {example_module} 不存在或无法加载 - {str(ie)}",
            )
        except Exception as e:
            logging.error(f"导入模块 {module_path} 时发生错误: {str(e)}")
            return (f"导入模块时发生错误: {module_path}", "0", f"❌ 错误: {str(e)}")

        # 检查是否包含construct_society函数
        if not hasattr(module, "construct_society"):
            logging.error(f"模块 {module_path} 中未找到 construct_society 函数")
            return (
                f"模块 {module_path} 中未找到 construct_society 函数",
                "0",
                "❌ 错误: 模块接口不兼容",
            )

        # 构建社会模拟
        try:
            logging.info("正在构建社会模拟...")
            society = module.construct_society(question)

        except Exception as e:
            logging.error(f"构建社会模拟时发生错误: {str(e)}")
            return (
                f"构建社会模拟时发生错误: {str(e)}",
                "0",
                f"❌ 错误: 构建失败 - {str(e)}",
            )

        # 运行社会模拟
        try:
            logging.info("正在运行社会模拟...")
            answer, chat_history, token_info = run_society(society)
            logging.info("社会模拟运行完成")
        except Exception as e:
            logging.error(f"运行社会模拟时发生错误: {str(e)}")
            return (
                f"运行社会模拟时发生错误: {str(e)}",
                "0",
                f"❌ 错误: 运行失败 - {str(e)}",
            )

        # 安全地获取令牌计数
        if not isinstance(token_info, dict):
            token_info = {}

        completion_tokens = token_info.get("completion_token_count", 0)
        prompt_tokens = token_info.get("prompt_token_count", 0)
        total_tokens = completion_tokens + prompt_tokens

        logging.info(
            f"处理完成，令牌使用: 完成={completion_tokens}, 提示={prompt_tokens}, 总计={total_tokens}"
        )

        return (
            answer,
            f"完成令牌: {completion_tokens:,} | 提示令牌: {prompt_tokens:,} | 总计: {total_tokens:,}",
            "✅ 成功完成",
        )

    except Exception as e:
        logging.error(f"处理问题时发生未捕获的错误: {str(e)}")
        return (f"发生错误: {str(e)}", "0", f"❌ 错误: {str(e)}")


def update_module_description(module_name: str) -> str:
    """返回所选模块的描述"""
    return MODULE_DESCRIPTIONS.get(module_name, "无可用描述")


# 存储前端配置的环境变量
WEB_FRONTEND_ENV_VARS: dict[str, str] = {}


def init_env_file():
    """初始化.env文件如果不存在"""
    dotenv_path = find_dotenv()
    if not dotenv_path:
        with open(".env", "w") as f:
            f.write(DEFAULT_ENV_TEMPLATE)
        dotenv_path = find_dotenv()
    return dotenv_path


def load_env_vars():
    """加载环境变量并返回字典格式

    Returns:
        dict: 环境变量字典，每个值为一个包含值和来源的元组 (value, source)
    """
    dotenv_path = init_env_file()
    load_dotenv(dotenv_path, override=True)

    # 从.env文件读取环境变量
    env_file_vars = {}
    with open(dotenv_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_file_vars[key.strip()] = value.strip().strip("\"'")

    # 从系统环境变量中获取
    system_env_vars = {
        k: v
        for k, v in os.environ.items()
        if k not in env_file_vars and k not in WEB_FRONTEND_ENV_VARS
    }

    # 合并环境变量，并标记来源
    env_vars = {}

    # 添加系统环境变量（最低优先级）
    for key, value in system_env_vars.items():
        env_vars[key] = (value, "系统")

    # 添加.env文件环境变量（中等优先级）
    for key, value in env_file_vars.items():
        env_vars[key] = (value, ".env文件")

    # 添加前端配置的环境变量（最高优先级）
    for key, value in WEB_FRONTEND_ENV_VARS.items():
        env_vars[key] = (value, "前端配置")
        # 确保操作系统环境变量也被更新
        os.environ[key] = value

    return env_vars


def save_env_vars(env_vars):
    """保存环境变量到.env文件

    Args:
        env_vars: 字典，键为环境变量名，值可以是字符串或(值,来源)元组
    """
    try:
        dotenv_path = init_env_file()

        # 保存每个环境变量
        for key, value_data in env_vars.items():
            if key and key.strip():  # 确保键不为空
                # 处理值可能是元组的情况
                if isinstance(value_data, tuple):
                    value = value_data[0]
                else:
                    value = value_data

                set_key(dotenv_path, key.strip(), value.strip())

        # 重新加载环境变量以确保生效
        load_dotenv(dotenv_path, override=True)

        return True, "环境变量已成功保存！"
    except Exception as e:
        return False, f"保存环境变量时出错: {str(e)}"


def add_env_var(key, value, from_frontend=True):
    """添加或更新单个环境变量

    Args:
        key: 环境变量名
        value: 环境变量值
        from_frontend: 是否来自前端配置，默认为True
    """
    try:
        if not key or not key.strip():
            return False, "变量名不能为空"

        key = key.strip()
        value = value.strip()

        # 如果来自前端，则添加到前端环境变量字典
        if from_frontend:
            WEB_FRONTEND_ENV_VARS[key] = value
            # 直接更新系统环境变量
            os.environ[key] = value

        # 同时更新.env文件
        dotenv_path = init_env_file()
        set_key(dotenv_path, key, value)
        load_dotenv(dotenv_path, override=True)

        return True, f"环境变量 {key} 已成功添加/更新！"
    except Exception as e:
        return False, f"添加环境变量时出错: {str(e)}"


def delete_env_var(key):
    """删除环境变量"""
    try:
        if not key or not key.strip():
            return False, "变量名不能为空"

        key = key.strip()

        # 从.env文件中删除
        dotenv_path = init_env_file()
        unset_key(dotenv_path, key)

        # 从前端环境变量字典中删除
        if key in WEB_FRONTEND_ENV_VARS:
            del WEB_FRONTEND_ENV_VARS[key]

        # 从当前进程环境中也删除
        if key in os.environ:
            del os.environ[key]

        return True, f"环境变量 {key} 已成功删除！"
    except Exception as e:
        return False, f"删除环境变量时出错: {str(e)}"


def is_api_related(key: str) -> bool:
    """判断环境变量是否与API相关

    Args:
        key: 环境变量名

    Returns:
        bool: 是否与API相关
    """
    # API相关的关键词
    api_keywords = [
        "api",
        "key",
        "token",
        "secret",
        "password",
        "openai",
        "qwen",
        "deepseek",
        "google",
        "search",
        "hf",
        "hugging",
        "chunkr",
        "firecrawl",
    ]

    # 检查是否包含API相关关键词（不区分大小写）
    return any(keyword in key.lower() for keyword in api_keywords)


def get_api_guide(key: str) -> str:
    """根据环境变量名返回对应的API获取指南

    Args:
        key: 环境变量名

    Returns:
        str: API获取指南链接或说明
    """
    key_lower = key.lower()
    if "openai" in key_lower:
        return "https://platform.openai.com/api-keys"
    elif "qwen" in key_lower or "dashscope" in key_lower:
        return "https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key"
    elif "deepseek" in key_lower:
        return "https://platform.deepseek.com/api_keys"
    elif "ppio" in key_lower:
        return "https://ppinfra.com/settings/key-management?utm_source=github_owl"
    elif "google" in key_lower:
        return "https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3"
    elif "search_engine_id" in key_lower:
        return "https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3"
    elif "chunkr" in key_lower:
        return "https://chunkr.ai/"
    elif "firecrawl" in key_lower:
        return "https://www.firecrawl.dev/"
    else:
        return ""


def update_env_table():
    """更新环境变量表格显示，只显示API相关的环境变量"""
    env_vars = load_env_vars()
    # 过滤出API相关的环境变量
    api_env_vars = {k: v for k, v in env_vars.items() if is_api_related(k)}
    # 转换为列表格式，以符合Gradio Dataframe的要求
    # 格式: [变量名, 变量值, 获取指南链接]
    result = []
    for k, v in api_env_vars.items():
        guide = get_api_guide(k)
        # 如果有指南链接，创建一个可点击的链接
        guide_link = (
            f"<a href='{guide}' target='_blank' class='guide-link'>🔗 获取</a>"
            if guide
            else ""
        )
        result.append([k, v[0], guide_link])
    return result


def save_env_table_changes(data):
    """保存环境变量表格的更改

    Args:
        data: Dataframe数据，可能是pandas DataFrame对象

    Returns:
        str: 操作状态信息，包含HTML格式的状态消息
    """
    try:
        logging.info(f"开始处理环境变量表格数据，类型: {type(data)}")

        # 获取当前所有环境变量
        current_env_vars = load_env_vars()
        processed_keys = set()  # 记录已处理的键，用于检测删除的变量

        # 处理pandas DataFrame对象
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            # 获取列名信息
            columns = data.columns.tolist()
            logging.info(f"DataFrame列名: {columns}")

            # 遍历DataFrame的每一行
            for index, row in data.iterrows():
                # 使用列名访问数据
                if len(columns) >= 3:
                    # 获取变量名和值 (第0列是变量名，第1列是值)
                    key = row[0] if isinstance(row, pd.Series) else row.iloc[0]
                    value = row[1] if isinstance(row, pd.Series) else row.iloc[1]

                    # 检查是否为空行或已删除的变量
                    if key and str(key).strip():  # 如果键名不为空，则添加或更新
                        logging.info(f"处理环境变量: {key} = {value}")
                        add_env_var(key, str(value))
                        processed_keys.add(key)
        # 处理其他格式
        elif isinstance(data, dict):
            logging.info(f"字典格式数据的键: {list(data.keys())}")
            # 如果是字典格式，尝试不同的键
            if "data" in data:
                rows = data["data"]
            elif "values" in data:
                rows = data["values"]
            elif "value" in data:
                rows = data["value"]
            else:
                # 尝试直接使用字典作为行数据
                rows = []
                for key, value in data.items():
                    if key not in ["headers", "types", "columns"]:
                        rows.append([key, value])

            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, list) and len(row) >= 2:
                        key, value = row[0], row[1]
                        if key and str(key).strip():
                            add_env_var(key, str(value))
                            processed_keys.add(key)
        elif isinstance(data, list):
            # 列表格式
            for row in data:
                if isinstance(row, list) and len(row) >= 2:
                    key, value = row[0], row[1]
                    if key and str(key).strip():
                        add_env_var(key, str(value))
                        processed_keys.add(key)
        else:
            logging.error(f"未知的数据格式: {type(data)}")
            return f"❌ 保存失败: 未知的数据格式 {type(data)}"

        # 处理删除的变量 - 检查当前环境变量中是否有未在表格中出现的变量
        api_related_keys = {k for k in current_env_vars.keys() if is_api_related(k)}
        keys_to_delete = api_related_keys - processed_keys

        # 删除不再表格中的变量
        for key in keys_to_delete:
            logging.info(f"删除环境变量: {key}")
            delete_env_var(key)

        return "✅ 环境变量已成功保存"
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logging.error(f"保存环境变量时出错: {str(e)}\n{error_details}")
        return f"❌ 保存失败: {str(e)}"


def get_env_var_value(key):
    """获取环境变量的实际值

    优先级：前端配置 > .env文件 > 系统环境变量
    """
    # 检查前端配置的环境变量
    if key in WEB_FRONTEND_ENV_VARS:
        return WEB_FRONTEND_ENV_VARS[key]

    # 检查系统环境变量（包括从.env加载的）
    return os.environ.get(key, "")


def create_ui():
    """创建增强版Gradio界面"""

    def clear_log_file():
        """清空日志文件内容"""
        try:
            if LOG_FILE and os.path.exists(LOG_FILE):
                # 清空日志文件内容而不是删除文件
                open(LOG_FILE, "w").close()
                logging.info("日志文件已清空")
                # 清空日志队列
                while not LOG_QUEUE.empty():
                    try:
                        LOG_QUEUE.get_nowait()
                    except queue.Empty:
                        break
                return ""
            else:
                return ""
        except Exception as e:
            logging.error(f"清空日志文件时出错: {str(e)}")
            return ""

    # 创建一个实时日志更新函数
    def process_with_live_logs(question, module_name):
        """处理问题并实时更新日志"""
        global CURRENT_PROCESS

        # 清空日志文件
        clear_log_file()

        # 创建一个后台线程来处理问题
        result_queue = queue.Queue()

        def process_in_background():
            try:
                result = run_owl(question, module_name)
                result_queue.put(result)
            except Exception as e:
                result_queue.put((f"发生错误: {str(e)}", "0", f"❌ 错误: {str(e)}"))

        # 启动后台处理线程
        bg_thread = threading.Thread(target=process_in_background)
        CURRENT_PROCESS = bg_thread  # 记录当前进程
        bg_thread.start()

        # 在等待处理完成的同时，每秒更新一次日志
        while bg_thread.is_alive():
            # 更新对话记录显示
            logs2 = get_latest_logs(100, LOG_QUEUE)

            # 始终更新状态
            yield (
                "0",
                "<span class='status-indicator status-running'></span> 处理中...",
                logs2,
            )

            time.sleep(1)

        # 处理完成，获取结果
        if not result_queue.empty():
            result = result_queue.get()
            answer, token_count, status = result

            # 最后一次更新对话记录
            logs2 = get_latest_logs(100, LOG_QUEUE)

            # 根据状态设置不同的指示器
            if "错误" in status:
                status_with_indicator = (
                    f"<span class='status-indicator status-error'></span> {status}"
                )
            else:
                status_with_indicator = (
                    f"<span class='status-indicator status-success'></span> {status}"
                )

            yield token_count, status_with_indicator, logs2
        else:
            logs2 = get_latest_logs(100, LOG_QUEUE)
            yield (
                "0",
                "<span class='status-indicator status-error'></span> 已终止",
                logs2,
            )

    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as app:
        gr.Markdown(
            """
                # 🦉 OWL 多智能体协作系统

                基于CAMEL框架开发的先进多智能体协作系统，旨在通过智能体协作解决复杂问题。

                可以通过修改本地脚本自定义模型和工具。
                
                本网页应用目前处于测试阶段，仅供演示和测试使用，尚未推荐用于生产环境。
                """
        )

        # 添加自定义CSS
        gr.HTML("""
            <style>
            /* 聊天容器样式 */
            .chat-container .chatbot {
                height: 500px;
                overflow-y: auto;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            

            /* 改进标签页样式 */
            .tabs .tab-nav {
                background-color: #f5f5f5;
                border-radius: 8px 8px 0 0;
                padding: 5px;
            }
            
            .tabs .tab-nav button {
                border-radius: 5px;
                margin: 0 3px;
                padding: 8px 15px;
                font-weight: 500;
            }
            
            .tabs .tab-nav button.selected {
                background-color: #2c7be5;
                color: white;
            }
            
            /* 状态指示器样式 */
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
            }
            
            .status-running {
                background-color: #ffc107;
                animation: pulse 1.5s infinite;
            }
            
            .status-success {
                background-color: #28a745;
            }
            
            .status-error {
                background-color: #dc3545;
            }
            
            /* 日志显示区域样式 */
            .log-display textarea {
                height: 400px !important;
                max-height: 400px !important;
                overflow-y: auto !important;
                font-family: monospace;
                font-size: 0.9em;
                white-space: pre-wrap;
                line-height: 1.4;
            }

            .log-display {
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                min-height: 50vh;
                max-height: 75vh;
            }
            
            /* 环境变量管理样式 */
            .env-manager-container {
                border-radius: 10px;
                padding: 15px;
                background-color: #f9f9f9;
                margin-bottom: 20px;
            }
            
            .env-controls, .api-help-container {
                border-radius: 8px;
                padding: 15px;
                background-color: white;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
                height: 100%;
            }
            
            .env-add-group, .env-delete-group {
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                background-color: #f5f8ff;
                border: 1px solid #e0e8ff;
            }
            
            .env-delete-group {
                background-color: #fff5f5;
                border: 1px solid #ffe0e0;
            }
            
            .env-buttons {
                justify-content: flex-start;
                gap: 10px;
                margin-top: 10px;
            }
            
            .env-button {
                min-width: 100px;
            }
            
            .delete-button {
                background-color: #dc3545;
                color: white;
            }
            
            .env-table {
                margin-bottom: 15px;
            }
            
            /* 改进环境变量表格样式 */
            .env-table table {
                border-collapse: separate;
                border-spacing: 0;
                width: 100%;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
            
            .env-table th {
                background-color: #f0f7ff;
                padding: 12px 15px;
                text-align: left;
                font-weight: 600;
                color: #2c7be5;
                border-bottom: 2px solid #e0e8ff;
            }
            
            .env-table td {
                padding: 10px 15px;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .env-table tr:hover td {
                background-color: #f9fbff;
            }
            
            .env-table tr:last-child td {
                border-bottom: none;
            }
            
            /* 状态图标样式 */
            .status-icon-cell {
                text-align: center;
                font-size: 1.2em;
            }
            
            /* 链接样式 */
            .guide-link {
                color: #2c7be5;
                text-decoration: none;
                cursor: pointer;
                font-weight: 500;
            }
            
            .guide-link:hover {
                text-decoration: underline;
            }
            
            .env-status {
                margin-top: 15px;
                font-weight: 500;
                padding: 10px;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            
            .env-status-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .env-status-error {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .api-help-accordion {
                margin-bottom: 8px;
                border-radius: 6px;
                overflow: hidden;
            }
            

            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            </style>
            """)

        with gr.Row():
            with gr.Column(scale=0.5):
                question_input = gr.Textbox(
                    lines=5,
                    placeholder="请输入您的问题...",
                    label="问题",
                    elem_id="question_input",
                    show_copy_button=True,
                    value="打开百度搜索，总结一下camel-ai的camel框架的github star、fork数目等，并把数字用plot包写成python文件保存到本地，并运行生成的python文件。",
                )

                # 增强版模块选择下拉菜单
                # 只包含MODULE_DESCRIPTIONS中定义的模块
                module_dropdown = gr.Dropdown(
                    choices=list(MODULE_DESCRIPTIONS.keys()),
                    value="run_qwen_zh",
                    label="选择功能模块",
                    interactive=True,
                )

                # 模块描述文本框
                module_description = gr.Textbox(
                    value=MODULE_DESCRIPTIONS["run_qwen_zh"],
                    label="模块描述",
                    interactive=False,
                    elem_classes="module-info",
                )

                with gr.Row():
                    run_button = gr.Button(
                        "运行", variant="primary", elem_classes="primary"
                    )

                status_output = gr.HTML(
                    value="<span class='status-indicator status-success'></span> 已就绪",
                    label="状态",
                )
                token_count_output = gr.Textbox(
                    label="令牌计数", interactive=False, elem_classes="token-count"
                )

                # 示例问题
                examples = [
                    "打开百度搜索，总结一下camel-ai的camel框架的github star、fork数目等，并把数字用plot包写成python文件保存到本地，并运行生成的python文件。",
                    "浏览亚马逊并找出一款对程序员有吸引力的产品。请提供产品名称和价格",
                    "写一个hello world的python文件，保存到本地",
                ]

                gr.Examples(examples=examples, inputs=question_input)

                gr.HTML("""
                        <div class="footer" id="about">
                            <h3>关于 OWL 多智能体协作系统</h3>
                            <p>OWL 是一个基于CAMEL框架开发的先进多智能体协作系统，旨在通过智能体协作解决复杂问题。</p>
                            <p>© 2025 CAMEL-AI.org. 基于Apache License 2.0开源协议</p>
                            <p><a href="https://github.com/camel-ai/owl" target="_blank">GitHub</a></p>
                        </div>
                    """)

            with gr.Tabs():  # 设置对话记录为默认选中的标签页
                with gr.TabItem("对话记录"):
                    # 添加对话记录显示区域
                    with gr.Group():
                        log_display2 = gr.Markdown(
                            value="暂无对话记录。",
                            elem_classes="log-display",
                        )

                    with gr.Row():
                        refresh_logs_button2 = gr.Button("刷新记录")
                        auto_refresh_checkbox2 = gr.Checkbox(
                            label="自动刷新", value=True, interactive=True
                        )
                        clear_logs_button2 = gr.Button("清空记录", variant="secondary")

                with gr.TabItem("环境变量管理", id="env-settings"):
                    with gr.Group(elem_classes="env-manager-container"):
                        gr.Markdown("""
                            ## 环境变量管理
                            
                            在此处设置模型API密钥和其他服务凭证。这些信息将保存在本地的`.env`文件中，确保您的API密钥安全存储且不会上传到网络。正确设置API密钥对于OWL系统的功能至关重要, 可以按找工具需求灵活配置环境变量。
                            """)

                        # 主要内容分为两列布局
                        with gr.Row():
                            # 左侧列：环境变量管理控件
                            with gr.Column(scale=3):
                                with gr.Group(elem_classes="env-controls"):
                                    # 环境变量表格 - 设置为可交互以直接编辑
                                    gr.Markdown("""
                                    <div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 10px; margin: 15px 0; border-radius: 4px;">
                                      <strong>提示：</strong> 请确保运行cp .env_template .env创建本地.env文件，根据运行模块灵活配置所需环境变量
                                    </div>
                                    """)

                                    # 增强版环境变量表格，支持添加和删除行
                                    env_table = gr.Dataframe(
                                        headers=["变量名", "值", "获取指南"],
                                        datatype=[
                                            "str",
                                            "str",
                                            "html",
                                        ],  # 将最后一列设置为html类型以支持链接
                                        row_count=10,  # 增加行数，以便添加新变量
                                        col_count=(3, "fixed"),
                                        value=update_env_table,
                                        label="API密钥和环境变量",
                                        interactive=True,  # 设置为可交互，允许直接编辑
                                        elem_classes="env-table",
                                    )

                                    # 操作说明
                                    gr.Markdown(
                                        """
                                    <div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 10px; margin: 15px 0; border-radius: 4px;">
                                    <strong>操作指南</strong>:
                                    <ul style="margin-top: 8px; margin-bottom: 8px;">
                                      <li><strong>编辑变量</strong>: 直接点击表格中的"值"单元格进行编辑</li>
                                      <li><strong>添加变量</strong>: 在空白行中输入新的变量名和值</li>
                                      <li><strong>删除变量</strong>: 清空变量名即可删除该行</li>
                                      <li><strong>获取API密钥</strong>: 点击"获取指南"列中的链接获取相应API密钥</li>
                                    </ul>
                                    </div>
                                    """,
                                        elem_classes="env-instructions",
                                    )

                                    # 环境变量操作按钮
                                    with gr.Row(elem_classes="env-buttons"):
                                        save_env_button = gr.Button(
                                            "💾 保存更改",
                                            variant="primary",
                                            elem_classes="env-button",
                                        )
                                        refresh_button = gr.Button(
                                            "🔄 刷新列表", elem_classes="env-button"
                                        )

                                    # 状态显示
                                    env_status = gr.HTML(
                                        label="操作状态",
                                        value="",
                                        elem_classes="env-status",
                                    )

                    # 连接事件处理函数
                    save_env_button.click(
                        fn=save_env_table_changes,
                        inputs=[env_table],
                        outputs=[env_status],
                    ).then(fn=update_env_table, outputs=[env_table])

                    refresh_button.click(fn=update_env_table, outputs=[env_table])

        # 设置事件处理
        run_button.click(
            fn=process_with_live_logs,
            inputs=[question_input, module_dropdown],
            outputs=[token_count_output, status_output, log_display2],
        )

        # 模块选择更新描述
        module_dropdown.change(
            fn=update_module_description,
            inputs=module_dropdown,
            outputs=module_description,
        )

        # 对话记录相关事件处理
        refresh_logs_button2.click(
            fn=lambda: get_latest_logs(100, LOG_QUEUE), outputs=[log_display2]
        )

        clear_logs_button2.click(fn=clear_log_file, outputs=[log_display2])

        # 自动刷新控制
        def toggle_auto_refresh(enabled):
            if enabled:
                return gr.update(every=3)
            else:
                return gr.update(every=0)

        auto_refresh_checkbox2.change(
            fn=toggle_auto_refresh,
            inputs=[auto_refresh_checkbox2],
            outputs=[log_display2],
        )

        # 不再默认自动刷新日志

    return app


# 主函数
def main():
    try:
        # 初始化日志系统
        global LOG_FILE
        LOG_FILE = setup_logging()
        logging.info("OWL Web应用程序启动")

        # 启动日志读取线程
        log_thread = threading.Thread(
            target=log_reader_thread, args=(LOG_FILE,), daemon=True
        )
        log_thread.start()
        logging.info("日志读取线程已启动")

        # 初始化.env文件（如果不存在）
        init_env_file()
        app = create_ui()

        app.queue()
        app.launch(server_name="0.0.0.0", server_port=7860, share=False)
    except Exception as e:
        logging.error(f"启动应用程序时发生错误: {str(e)}")
        print(f"启动应用程序时发生错误: {str(e)}")
        import traceback

        traceback.print_exc()

    finally:
        # 确保日志线程停止
        STOP_LOG_THREAD.set()
        STOP_REQUESTED.set()
        logging.info("应用程序关闭")


if __name__ == "__main__":
    main()
