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
# 正しいモジュールパスからインポート
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
import re

os.environ["PYTHONIOENCODING"] = "utf-8"


# ロギングシステムを設定
def setup_logging():
    """ログをファイル、メモリキュー、およびコンソールに出力するようにロギングシステムを設定"""
    # logsディレクトリを作成（存在しない場合）
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # ログファイル名を生成（現在の日付を使用）
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"gradio_log_{current_date}.txt")

    # ルートロガーを設定（すべてのログをキャプチャ）
    root_logger = logging.getLogger()

    # 重複ログを避けるために既存のハンドラをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(logging.INFO)

    # ファイルハンドラを作成
    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.INFO)

    # コンソールハンドラを作成
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # フォーマッタを作成
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("ログシステムが初期化されました、ログファイル: %s", log_file)
    return log_file


# グローバル変数
LOG_FILE = None
LOG_QUEUE: queue.Queue = queue.Queue()  # ログキュー
STOP_LOG_THREAD = threading.Event()
CURRENT_PROCESS = None  # 現在実行中のプロセスを追跡するために使用
STOP_REQUESTED = threading.Event()  # 停止が要求されたかどうかをマークするために使用


# ログの読み取りと更新の関数
def log_reader_thread(log_file):
    """継続的にログファイルを読み取り、新しい行をキューに追加するバックグラウンドスレッド"""
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # ファイルの末尾に移動
            f.seek(0, 2)

            while not STOP_LOG_THREAD.is_set():
                line = f.readline()
                if line:
                    LOG_QUEUE.put(line)  # 会話記録キューに追加
                else:
                    # 新しい行がない場合は短時間待機
                    time.sleep(0.1)
    except Exception as e:
        logging.error(f"ログリーダースレッドエラー: {str(e)}")


def get_latest_logs(max_lines=100, queue_source=None):
    """キューから最新のログ行を取得するか、キューが空の場合はファイルから直接読み取る

    引数:
        max_lines: 返す最大行数
        queue_source: 使用するキューを指定、デフォルトはLOG_QUEUE

    戻り値:
        str: ログ内容
    """
    logs = []
    log_queue = queue_source if queue_source else LOG_QUEUE

    # 元のキューから削除せずに処理できるように、ログを保存する一時キューを作成
    temp_queue = queue.Queue()
    temp_logs = []

    try:
        # キューから利用可能なすべてのログ行を取得
        while not log_queue.empty() and len(temp_logs) < max_lines:
            log = log_queue.get_nowait()
            temp_logs.append(log)
            temp_queue.put(log)  # ログを一時キューに戻す
    except queue.Empty:
        pass

    # 会話記録を処理
    logs = temp_logs

    # 新しいログがないか、十分なログがない場合は、ファイルから直接最後の数行を読み取る
    if len(logs) < max_lines and LOG_FILE and os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                # キューにすでにいくつかのログがある場合は、必要な残りの行だけを読み取る
                remaining_lines = max_lines - len(logs)
                file_logs = (
                    all_lines[-remaining_lines:]
                    if len(all_lines) > remaining_lines
                    else all_lines
                )

                # ファイルログをキューログの前に追加
                logs = file_logs + logs
        except Exception as e:
            error_msg = f"ログファイルの読み取りエラー: {str(e)}"
            logging.error(error_msg)
            if not logs:  # ログがない場合のみエラーメッセージを追加
                logs = [error_msg]

    # まだログがない場合は、プロンプトメッセージを返す
    if not logs:
        return "初期化中..."

    # ログをフィルタリングし、'camel.agents.chat_agent - INFO'を含むログのみを保持
    filtered_logs = []
    for log in logs:
        if "camel.agents.chat_agent - INFO" in log:
            filtered_logs.append(log)

    # フィルタリング後にログがない場合は、プロンプトメッセージを返す
    if not filtered_logs:
        return "まだ会話記録はありません。"

    # Process log content, extract the latest user and assistant messages
    simplified_logs = []

    # Use a set to track messages that have already been processed, to avoid duplicates
    processed_messages = set()

    def process_message(role, content):
        # Create a unique identifier to track messages
        msg_id = f"{role}:{content}"
        if msg_id in processed_messages:
            return None

        processed_messages.add(msg_id)
        content = content.replace("\\n", "\n")
        lines = [line.strip() for line in content.split("\n")]
        content = "\n".join(lines)

        role_emoji = "🙋" if role.lower() == "user" else "🤖"
        role_ja = "ユーザー" if role.lower() == "user" else "アシスタント"
        return f"""### {role_emoji} {role_ja}エージェント

{content}"""

    for log in filtered_logs:
        formatted_messages = []
        # Try to extract message array
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

        # If JSON parsing fails or no message array is found, try to extract conversation content directly
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

    # Format log output, ensure appropriate separation between each conversation record
    formatted_logs = []
    for i, log in enumerate(simplified_logs):
        # Remove excess whitespace characters from beginning and end
        log = log.strip()

        formatted_logs.append(log)

        # Ensure each conversation record ends with a newline
        if not log.endswith("\n"):
            formatted_logs.append("\n")

    return "\n".join(formatted_logs)


# モジュールの説明を含む辞書
MODULE_DESCRIPTIONS = {
    "run": "デフォルトモード: OpenAIモデルのデフォルトエージェント協力モードを使用し、ほとんどのタスクに適しています。",
    "run_mini": "最小限の設定でOpenAIモデルを使用してタスクを処理します",
    "run_deepseek_zh": "中国語タスクを処理するためにdeepseekモデルを使用します",
    "run_openai_compatible_model": "OpenAI互換モデルを使用してタスクを処理します",
    "run_ollama": "ローカルのollamaモデルを使用してタスクを処理します",
    "run_qwen_mini_zh": "最小限の設定でqwenモデルを使用してタスクを処理します",
    "run_qwen_zh": "qwenモデルを使用して中国語タスクを処理します",
    "run_azure_openai": "Azure OpenAIモデルを使用してタスクを処理します",
    "run_groq": "groqモデルを使用してタスクを処理します",
    "run_together_ai": "together aiモデルを使用してタスクを処理します",
}


# デフォルトの環境変数テンプレート
DEFAULT_ENV_TEMPLATE = """#===========================================
# モデル & API 
# (参照: https://docs.camel-ai.org/key_modules/models.html#)
#===========================================

# OPENAI API (https://platform.openai.com/api-keys)
OPENAI_API_KEY='あなたのキー'
# OPENAI_API_BASE_URL=""

# Azure OpenAI API
# AZURE_OPENAI_BASE_URL=""
# AZURE_API_VERSION=""
# AZURE_OPENAI_API_KEY=""
# AZURE_DEPLOYMENT_NAME=""


# Qwen API (https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key)
QWEN_API_KEY='あなたのキー'

# DeepSeek API (https://platform.deepseek.com/api_keys)
DEEPSEEK_API_KEY='あなたのキー'

#===========================================
# ツール & サービス API
#===========================================

# Google Search API (https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3)
GOOGLE_API_KEY='あなたのキー'
SEARCH_ENGINE_ID='あなたのID'

# Chunkr API (https://chunkr.ai/)
CHUNKR_API_KEY='あなたのキー'

# Firecrawl API (https://www.firecrawl.dev/)
FIRECRAWL_API_KEY='あなたのキー'
#FIRECRAWL_API_URL="https://api.firecrawl.dev"
"""


def validate_input(question: str) -> bool:
    """ユーザー入力が有効かどうかを検証

    引数:
        question: ユーザーの質問

    戻り値:
        bool: 入力が有効かどうか
    """
    # 入力が空またはスペースのみかどうかをチェック
    if not question or question.strip() == "":
        return False
    return True


def run_owl(question: str, example_module: str) -> Tuple[str, str, str]:
    """OWLシステムを実行して結果を返す

    引数:
        question: ユーザーの質問
        example_module: インポートする例モジュール名（例："run_terminal_zh"や"run_deep"）

    戻り値:
        Tuple[...]: 回答、トークン数、ステータス
    """
    global CURRENT_PROCESS

    # Validate input
    if not validate_input(question):
        logging.warning("ユーザーが無効な入力を送信しました")
        return (
            "有効な質問を入力してください",
            "0",
            "❌ エラー: 無効な入力質問",
        )

    try:
        # Ensure environment variables are loaded
        load_dotenv(find_dotenv(), override=True)
        logging.info(f"質問を処理中: '{question}', モジュール使用: {example_module}")

        # Check if the module is in MODULE_DESCRIPTIONS
        if example_module not in MODULE_DESCRIPTIONS:
            logging.error(
                f"ユーザーがサポートされていないモジュールを選択しました: {example_module}"
            )
            return (
                f"選択されたモジュール '{example_module}' はサポートされていません",
                "0",
                "❌ エラー: サポートされていないモジュール",
            )

        # Dynamically import target module
        module_path = f"examples.{example_module}"
        try:
            logging.info(f"モジュールをインポート中: {module_path}")
            module = importlib.import_module(module_path)
        except ImportError as ie:
            logging.error(f"モジュール {module_path} をインポートできません: {str(ie)}")
            return (
                f"モジュールをインポートできません: {module_path}",
                "0",
                f"❌ エラー: モジュール {example_module} が存在しないか、読み込めません - {str(ie)}",
            )
        except Exception as e:
            logging.error(
                f"モジュール {module_path} のインポート中にエラーが発生しました: {str(e)}"
            )
            return (
                f"モジュールのインポート中にエラーが発生しました: {module_path}",
                "0",
                f"❌ エラー: {str(e)}",
            )

        # Check if it contains the construct_society function
        if not hasattr(module, "construct_society"):
            logging.error(
                f"construct_society 関数がモジュール {module_path} に見つかりません"
            )
            return (
                f"construct_society 関数がモジュール {module_path} に見つかりません",
                "0",
                "❌ エラー: モジュールインターフェースが互換性がありません",
            )

        # Build society simulation
        try:
            logging.info("社会シミュレーションを構築中...")
            society = module.construct_society(question)

        except Exception as e:
            logging.error(
                f"社会シミュレーションの構築中にエラーが発生しました: {str(e)}"
            )
            return (
                f"社会シミュレーションの構築中にエラーが発生しました: {str(e)}",
                "0",
                f"❌ エラー: 構築に失敗しました - {str(e)}",
            )

        # Run society simulation
        try:
            logging.info("社会シミュレーションを実行中...")
            answer, chat_history, token_info = run_society(society)
            logging.info("社会シミュレーションが完了しました")
        except Exception as e:
            logging.error(
                f"社会シミュレーションの実行中にエラーが発生しました: {str(e)}"
            )
            return (
                f"社会シミュレーションの実行中にエラーが発生しました: {str(e)}",
                "0",
                f"❌ エラー: 実行に失敗しました - {str(e)}",
            )

        # Safely get token count
        if not isinstance(token_info, dict):
            token_info = {}

        completion_tokens = token_info.get("completion_token_count", 0)
        prompt_tokens = token_info.get("prompt_token_count", 0)
        total_tokens = completion_tokens + prompt_tokens

        logging.info(
            f"処理が完了しました、トークン使用量: 完了={completion_tokens}, プロンプト={prompt_tokens}, 合計={total_tokens}"
        )

        return (
            answer,
            f"完了トークン: {completion_tokens:,} | プロンプトトークン: {prompt_tokens:,} | 合計: {total_tokens:,}",
            "✅ 正常に完了しました",
        )

    except Exception as e:
        logging.error(f"質問の処理中に予期しないエラーが発生しました: {str(e)}")
        return (f"エラーが発生しました: {str(e)}", "0", f"❌ エラー: {str(e)}")


def update_module_description(module_name: str) -> str:
    """選択されたモジュールの説明を返す"""
    return MODULE_DESCRIPTIONS.get(module_name, "説明はありません")


# フロントエンドから設定された環境変数を保存
WEB_FRONTEND_ENV_VARS: dict[str, str] = {}


def init_env_file():
    """.envファイルが存在しない場合に初期化する"""
    dotenv_path = find_dotenv()
    if not dotenv_path:
        with open(".env", "w") as f:
            f.write(DEFAULT_ENV_TEMPLATE)
        dotenv_path = find_dotenv()
    return dotenv_path


def load_env_vars():
    """環境変数を読み込み、辞書形式で返す

    戻り値:
        dict: 環境変数辞書、各値は値とソースを含むタプル（value, source）
    """
    dotenv_path = init_env_file()
    load_dotenv(dotenv_path, override=True)

    # .envファイルから環境変数を読み込む
    env_file_vars = {}
    with open(dotenv_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_file_vars[key.strip()] = value.strip().strip("\"'")

    # システム環境変数から取得
    system_env_vars = {
        k: v
        for k, v in os.environ.items()
        if k not in env_file_vars and k not in WEB_FRONTEND_ENV_VARS
    }

    # 環境変数をマージしてソースをマーク
    env_vars = {}

    # システム環境変数を追加（最低優先度）
    for key, value in system_env_vars.items():
        env_vars[key] = (value, "システム")

    # .envファイル環境変数を追加（中程度の優先度）
    for key, value in env_file_vars.items():
        env_vars[key] = (value, ".envファイル")

    # フロントエンドで設定された環境変数を追加（最高優先度）
    for key, value in WEB_FRONTEND_ENV_VARS.items():
        env_vars[key] = (value, "フロントエンド設定")
        # オペレーティングシステムの環境変数も更新されていることを確認
        os.environ[key] = value

    return env_vars


def save_env_vars(env_vars):
    """環境変数を.envファイルに保存

    引数:
        env_vars: 辞書、キーは環境変数名、値は文字列または（value, source）タプル
    """
    try:
        dotenv_path = init_env_file()

        # Save each environment variable
        for key, value_data in env_vars.items():
            if key and key.strip():  # Ensure key is not empty
                # Handle case where value might be a tuple
                if isinstance(value_data, tuple):
                    value = value_data[0]
                else:
                    value = value_data

                set_key(dotenv_path, key.strip(), value.strip())

        # Reload environment variables to ensure they take effect
        load_dotenv(dotenv_path, override=True)

        return True, "環境変数が正常に保存されました！"
    except Exception as e:
        return False, f"環境変数の保存中にエラーが発生しました: {str(e)}"


def add_env_var(key, value, from_frontend=True):
    """単一の環境変数を追加または更新

    引数:
        key: 環境変数名
        value: 環境変数値
        from_frontend: フロントエンド設定からかどうか、デフォルトはTrue
    """
    try:
        if not key or not key.strip():
            return False, "変数名は空にできません"

        key = key.strip()
        value = value.strip()

        # If from frontend, add to frontend environment variable dictionary
        if from_frontend:
            WEB_FRONTEND_ENV_VARS[key] = value
            # Directly update system environment variables
            os.environ[key] = value

        # Also update .env file
        dotenv_path = init_env_file()
        set_key(dotenv_path, key, value)
        load_dotenv(dotenv_path, override=True)

        return True, f"環境変数 {key} が正常に追加/更新されました！"
    except Exception as e:
        return False, f"環境変数の追加中にエラーが発生しました: {str(e)}"


def delete_env_var(key):
    """環境変数を削除"""
    try:
        if not key or not key.strip():
            return False, "変数名は空にできません"

        key = key.strip()

        # Delete from .env file
        dotenv_path = init_env_file()
        unset_key(dotenv_path, key)

        # Delete from frontend environment variable dictionary
        if key in WEB_FRONTEND_ENV_VARS:
            del WEB_FRONTEND_ENV_VARS[key]

        # Also delete from current process environment
        if key in os.environ:
            del os.environ[key]

        return True, f"環境変数 {key} が正常に削除されました！"
    except Exception as e:
        return False, f"環境変数の削除中にエラーが発生しました: {str(e)}"


def is_api_related(key: str) -> bool:
    """環境変数がAPI関連かどうかを判断

    引数:
        key: 環境変数名

    戻り値:
        bool: API関連かどうか
    """
    # API関連キーワード
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

    # API関連キーワードが含まれているか確認（大文字小文字を区別しない）
    return any(keyword in key.lower() for keyword in api_keywords)


def get_api_guide(key: str) -> str:
    """環境変数名に基づいて対応するAPIガイドを返す

    引数:
        key: 環境変数名

    戻り値:
        str: APIガイドリンクまたは説明
    """
    key_lower = key.lower()
    if "openai" in key_lower:
        return "https://platform.openai.com/api-keys"
    elif "qwen" in key_lower or "dashscope" in key_lower:
        return "https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key"
    elif "deepseek" in key_lower:
        return "https://platform.deepseek.com/api_keys"
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
    """環境変数テーブル表示を更新し、API関連の環境変数のみを表示"""
    env_vars = load_env_vars()
    # Filter out API-related environment variables
    api_env_vars = {k: v for k, v in env_vars.items() if is_api_related(k)}
    # Convert to list format to meet Gradio Dataframe requirements
    # Format: [Variable name, Variable value, Guide link]
    result = []
    for k, v in api_env_vars.items():
        guide = get_api_guide(k)
        # If there's a guide link, create a clickable link
        guide_link = (
            f"<a href='{guide}' target='_blank' class='guide-link'>🔗 取得</a>"
            if guide
            else ""
        )
        result.append([k, v[0], guide_link])
    return result


def save_env_table_changes(data):
    """環境変数テーブルへの変更を保存

    引数:
        data: データフレームデータ、おそらくpandas DataFrameオブジェクト

    戻り値:
        str: 操作ステータス情報、HTML形式のステータスメッセージを含む
    """
    try:
        logging.info(f"環境変数テーブルデータの処理を開始します、タイプ: {type(data)}")

        # Get all current environment variables
        current_env_vars = load_env_vars()
        processed_keys = set()  # Record processed keys to detect deleted variables

        # Process pandas DataFrame object
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            # Get column name information
            columns = data.columns.tolist()
            logging.info(f"DataFrameの列名: {columns}")

            # Iterate through each row of the DataFrame
            for index, row in data.iterrows():
                # Use column names to access data
                if len(columns) >= 3:
                    # Get variable name and value (column 0 is name, column 1 is value)
                    key = row[0] if isinstance(row, pd.Series) else row.iloc[0]
                    value = row[1] if isinstance(row, pd.Series) else row.iloc[1]

                    # Check if it's an empty row or deleted variable
                    if (
                        key and str(key).strip()
                    ):  # If key name is not empty, add or update
                        logging.info(f"環境変数の処理: {key} = {value}")
                        add_env_var(key, str(value))
                        processed_keys.add(key)
        # Process other formats
        elif isinstance(data, dict):
            logging.info(f"辞書形式データのキー: {list(data.keys())}")
            # If dictionary format, try different keys
            if "data" in data:
                rows = data["data"]
            elif "values" in data:
                rows = data["values"]
            elif "value" in data:
                rows = data["value"]
            else:
                # Try using dictionary directly as row data
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
            logging.error(f"不明なデータ形式: {type(data)}")
            return f"❌ 保存に失敗しました: 不明なデータ形式 {type(data)}"

        # Process deleted variables - check if there are variables in current environment not appearing in the table
        api_related_keys = {k for k in current_env_vars.keys() if is_api_related(k)}
        keys_to_delete = api_related_keys - processed_keys

        # Delete variables no longer in the table
        for key in keys_to_delete:
            logging.info(f"環境変数の削除: {key}")
            delete_env_var(key)

        return "✅ 環境変数が正常に保存されました"
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logging.error(
            f"環境変数の保存中にエラーが発生しました: {str(e)}\n{error_details}"
        )
        return f"❌ 保存に失敗しました: {str(e)}"


def get_env_var_value(key):
    """環境変数の実際の値を取得

    優先順位: フロントエンド設定 > .envファイル > システム環境変数
    """
    # Check frontend configured environment variables
    if key in WEB_FRONTEND_ENV_VARS:
        return WEB_FRONTEND_ENV_VARS[key]

    # Check system environment variables (including those loaded from .env)
    return os.environ.get(key, "")


def create_ui():
    """拡張されたGradioインターフェースを作成"""

    def clear_log_file():
        """ログファイルの内容をクリア"""
        try:
            if LOG_FILE and os.path.exists(LOG_FILE):
                # Clear log file content instead of deleting the file
                open(LOG_FILE, "w").close()
                logging.info("ログファイルがクリアされました")
                # Clear log queue
                while not LOG_QUEUE.empty():
                    try:
                        LOG_QUEUE.get_nowait()
                    except queue.Empty:
                        break
                return ""
            else:
                return ""
        except Exception as e:
            logging.error(f"ログファイルのクリア中にエラーが発生しました: {str(e)}")
            return ""

    # リアルタイムログ更新関数を作成
    def process_with_live_logs(question, module_name):
        """質問を処理し、リアルタイムでログを更新"""
        global CURRENT_PROCESS

        # Clear log file
        clear_log_file()

        # 質問を処理するバックグラウンドスレッドを作成
        result_queue = queue.Queue()

        def process_in_background():
            try:
                result = run_owl(question, module_name)
                result_queue.put(result)
            except Exception as e:
                result_queue.put(
                    (f"エラーが発生しました: {str(e)}", "0", f"❌ エラー: {str(e)}")
                )

        # バックグラウンド処理スレッドを開始
        bg_thread = threading.Thread(target=process_in_background)
        CURRENT_PROCESS = bg_thread  # 現在のプロセスを記録
        bg_thread.start()

        # 処理が完了するのを待つ間、1秒ごとにログを更新
        while bg_thread.is_alive():
            # 会話記録表示を更新
            logs2 = get_latest_logs(100, LOG_QUEUE)

            # Always update status
            yield (
                "0",
                "<span class='status-indicator status-running'></span> 処理中...",
                logs2,
            )

            time.sleep(1)

        # Processing complete, get results
        if not result_queue.empty():
            result = result_queue.get()
            answer, token_count, status = result

            # Final update of conversation record
            logs2 = get_latest_logs(100, LOG_QUEUE)

            # Set different indicators based on status
            if "エラー" in status:
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
                "<span class='status-indicator status-error'></span> 終了しました",
                logs2,
            )

    with gr.Blocks(title="OWL", theme=gr.themes.Soft(primary_hue="blue")) as app:
        gr.Markdown(
            """
                # 🦉 OWL マルチエージェント協力システム

                CAMELフレームワークをベースに開発された高度なマルチエージェント協力システムで、エージェント協力を通じて複雑な問題を解決するように設計されています。

                モデルやツールはローカルスクリプトを変更することでカスタマイズできます。
                
                このウェブアプリは現在ベータ開発中です。デモンストレーションとテスト目的のみで提供されており、本番環境での使用はまだ推奨されていません。
                """
        )

        # Add custom CSS
        gr.HTML("""
            <style>
            /* Chat container style */
            .chat-container .chatbot {
                height: 500px;
                overflow-y: auto;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            

            /* Improved tab style */
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
            
            /* Status indicator style */
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
            
            /* Log display area style */
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
            
            /* Environment variable management style */
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
            
            /* Improved environment variable table style */
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
            
            /* Status icon style */
            .status-icon-cell {
                text-align: center;
                font-size: 1.2em;
            }
            
            /* Link style */
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
                    placeholder="質問を入力してください...",
                    label="質問",
                    elem_id="question_input",
                    show_copy_button=True,
                    value="Googleで検索して、camel-aiのcamelフレームワークのGitHubスター数、フォーク数などを要約し、その数値をplotパッケージを使ってPythonファイルに書き込み、ローカルに保存して、生成したPythonファイルを実行してください。",
                )

                # Enhanced module selection dropdown
                # Only includes modules defined in MODULE_DESCRIPTIONS
                module_dropdown = gr.Dropdown(
                    choices=list(MODULE_DESCRIPTIONS.keys()),
                    value="run",
                    label="機能モジュールを選択",
                    interactive=True,
                )

                # Module description text box
                module_description = gr.Textbox(
                    value=MODULE_DESCRIPTIONS["run"],
                    label="モジュールの説明",
                    interactive=False,
                    elem_classes="module-info",
                )

                with gr.Row():
                    run_button = gr.Button(
                        "実行", variant="primary", elem_classes="primary"
                    )

                status_output = gr.HTML(
                    value="<span class='status-indicator status-success'></span> 準備完了",
                    label="ステータス",
                )
                token_count_output = gr.Textbox(
                    label="トークン数", interactive=False, elem_classes="token-count"
                )

                # Example questions
                examples = [
                    "Googleで検索して、camel-aiのcamelフレームワークのGitHubスター数、フォーク数などを要約し、その数値をplotパッケージを使ってPythonファイルに書き込み、ローカルに保存して、生成したPythonファイルを実行してください。",
                    "Amazonを閲覧して、プログラマーに魅力的な商品を見つけてください。商品名と価格を提供してください",
                    "Hello worldを表示するPythonファイルを作成し、ローカルに保存してください",
                ]

                gr.Examples(examples=examples, inputs=question_input)

                gr.HTML("""
                        <div class="footer" id="about">
                            <h3>OWLマルチエージェント協力システムについて</h3>
                            <p>OWLはCAMELフレームワークをベースに開発された高度なマルチエージェント協力システムで、エージェント協力を通じて複雑な問題を解決するように設計されています。</p>
                            <p>© 2025 CAMEL-AI.org. Apache License 2.0オープンソースライセンスに基づいています</p>
                            <p><a href="https://github.com/camel-ai/owl" target="_blank">GitHub</a></p>
                        </div>
                    """)

            with gr.Tabs():  # Set conversation record as the default selected tab
                with gr.TabItem("会話記録"):
                    # Add conversation record display area
                    with gr.Group():
                        log_display2 = gr.Markdown(
                            value="まだ会話記録はありません。",
                            elem_classes="log-display",
                        )

                    with gr.Row():
                        refresh_logs_button2 = gr.Button("記録を更新")
                        auto_refresh_checkbox2 = gr.Checkbox(
                            label="自動更新", value=True, interactive=True
                        )
                        clear_logs_button2 = gr.Button(
                            "記録をクリア", variant="secondary"
                        )

                with gr.TabItem("環境変数管理", id="env-settings"):
                    with gr.Group(elem_classes="env-manager-container"):
                        gr.Markdown("""
                            ## 環境変数管理
                            
                            ここでモデルAPIキーやその他のサービス認証情報を設定します。この情報はローカルの`.env`ファイルに保存され、APIキーが安全に保存され、ネットワークにアップロードされないことを保証します。APIキーを正しく設定することは、OWLシステムの機能にとって非常に重要です。環境変数はツールの要件に応じて柔軟に設定できます。
                            """)

                        # Main content divided into two-column layout
                        with gr.Row():
                            # Left column: Environment variable management controls
                            with gr.Column(scale=3):
                                with gr.Group(elem_classes="env-controls"):
                                    # Environment variable table - set to interactive for direct editing
                                    gr.Markdown("""
                                    <div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 10px; margin: 15px 0; border-radius: 4px;">
                                      <strong>ヒント:</strong> cp .env_template .env を実行してローカルの.envファイルを作成し、実行モジュールに応じて必要な環境変数を柔軟に設定してください
                                    </div>
                                    """)

                                    # Enhanced environment variable table, supporting adding and deleting rows
                                    env_table = gr.Dataframe(
                                        headers=[
                                            "変数名",
                                            "値",
                                            "取得ガイド",
                                        ],
                                        datatype=[
                                            "str",
                                            "str",
                                            "html",
                                        ],  # Set the last column as HTML type to support links
                                        row_count=10,  # Increase row count to allow adding new variables
                                        col_count=(3, "fixed"),
                                        value=update_env_table,
                                        label="APIキーと環境変数",
                                        interactive=True,  # Set as interactive, allowing direct editing
                                        elem_classes="env-table",
                                    )

                                    # Operation instructions
                                    gr.Markdown(
                                        """
                                    <div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 10px; margin: 15px 0; border-radius: 4px;">
                                    <strong>操作ガイド</strong>:
                                    <ul style="margin-top: 8px; margin-bottom: 8px;">
                                      <li><strong>変数の編集</strong>: テーブルの「値」セルを直接クリックして編集</li>
                                      <li><strong>変数の追加</strong>: 空白行に新しい変数名と値を入力</li>
                                      <li><strong>変数の削除</strong>: 変数名をクリアしてその行を削除</li>
                                      <li><strong>APIキーの取得</strong>: 「取得ガイド」列のリンクをクリックして対応するAPIキーを取得</li>
                                    </ul>
                                    </div>
                                    """,
                                        elem_classes="env-instructions",
                                    )

                                    # Environment variable operation buttons
                                    with gr.Row(elem_classes="env-buttons"):
                                        save_env_button = gr.Button(
                                            "💾 変更を保存",
                                            variant="primary",
                                            elem_classes="env-button",
                                        )
                                        refresh_button = gr.Button(
                                            "🔄 リストを更新", elem_classes="env-button"
                                        )

                                    # Status display
                                    env_status = gr.HTML(
                                        label="操作ステータス",
                                        value="",
                                        elem_classes="env-status",
                                    )

                    # 連接事件処理函数
                    save_env_button.click(
                        fn=save_env_table_changes,
                        inputs=[env_table],
                        outputs=[env_status],
                    ).then(fn=update_env_table, outputs=[env_table])

                    refresh_button.click(fn=update_env_table, outputs=[env_table])

        # Set up event handling
        run_button.click(
            fn=process_with_live_logs,
            inputs=[question_input, module_dropdown],
            outputs=[token_count_output, status_output, log_display2],
        )

        # Module selection updates description
        module_dropdown.change(
            fn=update_module_description,
            inputs=module_dropdown,
            outputs=module_description,
        )

        # Conversation record related event handling
        refresh_logs_button2.click(
            fn=lambda: get_latest_logs(100, LOG_QUEUE), outputs=[log_display2]
        )

        clear_logs_button2.click(fn=clear_log_file, outputs=[log_display2])

        # Auto refresh control
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

        # No longer automatically refresh logs by default

    return app


# メイン関数
def main():
    try:
        # ロギングシステムを初期化
        global LOG_FILE
        LOG_FILE = setup_logging()
        logging.info("OWL Webアプリケーションが開始されました")

        # ログ読み取りスレッドを開始
        log_thread = threading.Thread(
            target=log_reader_thread, args=(LOG_FILE,), daemon=True
        )
        log_thread.start()
        logging.info("ログ読み取りスレッドが開始されました")

        # .envファイルを初期化（存在しない場合）
        init_env_file()
        app = create_ui()

        app.queue()
        app.launch(
            share=False,
            favicon_path=os.path.join(
                os.path.dirname(__file__), "assets", "owl-favicon.ico"
            ),
        )
    except Exception as e:
        logging.error(f"アプリケーションの起動中にエラーが発生しました: {str(e)}")
        print(f"アプリケーションの起動中にエラーが発生しました: {str(e)}")
        import traceback

        traceback.print_exc()

    finally:
        # ログスレッドが停止することを確認
        STOP_LOG_THREAD.set()
        STOP_REQUESTED.set()
        logging.info("アプリケーションが終了しました")


if __name__ == "__main__":
    main()
