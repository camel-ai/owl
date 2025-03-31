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
import sys

sys.path.append("../")

import re
from typing import Optional
from camel.logger import get_logger

logger = get_logger(__name__)


def extract_pattern(content: str, pattern: str) -> Optional[str]:
    """从给定的文本内容中提取指定的标签包裹的文本内容。

    Args:
        content (str): 需要解析的原始文本内容。
        pattern (str): 需要匹配的标签名称，例如"answer"会匹配<answer>...</answer>。

    Returns:
        Optional[str]: 匹配到的文本内容（去除首尾空白），若未找到或发生错误则返回None。
    """
    try:
        # 构建正则表达式模式，匹配指定标签包裹的内容（允许跨行）
        _pattern = rf"<{pattern}>(.*?)</{pattern}>"
        match = re.search(_pattern, content, re.DOTALL)
        if match:
            text = match.group(1)
            return text.strip()
        else:
            return None
    except Exception as e:
        # 记录错误信息并返回None
        logger.warning(f"Error extracting answer: {e}, current content: {content}")
        return None
