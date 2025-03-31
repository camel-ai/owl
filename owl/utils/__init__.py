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

from .common import extract_pattern
from .enhanced_role_playing import (
    OwlRolePlaying,
    OwlGAIARolePlaying,
    run_society,
    arun_society,
)
from .gaia import GAIABenchmark
from .document_toolkit import DocumentProcessingToolkit

# 模块导出的公共接口列表
__all__ = [
    "extract_pattern",
    "OwlRolePlaying",
    "OwlGAIARolePlaying",
    "run_society",
    "arun_society",
    "GAIABenchmark",
    "DocumentProcessingToolkit",
]

# 函数：extract_pattern
"""
从给定文本中提取符合特定模式的内容。

参数:
    text (str): 需要提取模式的原始文本。
    pattern (str): 用于匹配的正则表达式模式。

返回:
    list: 包含所有匹配结果的列表，如果未找到匹配项，则返回空列表。
"""

# 类：OwlRolePlaying
"""
用于实现角色扮演功能的基础类。

该类提供角色扮演的核心逻辑，支持多种角色交互场景。
"""

# 类：OwlGAIARolePlaying
"""
继承自 OwlRolePlaying 的增强版角色扮演类。

在基础角色扮演功能的基础上，集成了与 GAIA 相关的扩展功能，
适用于更复杂的社会模拟和互动场景。
"""

# 函数：run_society
"""
运行一个同步的社会模拟环境。

参数:
    config (dict): 社会模拟的配置参数，包括角色、规则和其他环境设置。

返回:
    dict: 社会模拟的结果数据，包含角色行为、事件记录等信息。
"""

# 函数：arun_society
"""
运行一个异步的社会模拟环境。

参数:
    config (dict): 社会模拟的配置参数，包括角色、规则和其他环境设置。

返回:
    asyncio.Future: 异步任务对象，包含社会模拟的结果数据。
"""

# 类：GAIABenchmark
"""
用于评估和测试 GAIA 系统性能的基准工具。

提供多种测试用例和评估指标，帮助开发者优化系统性能。
"""

# 类：DocumentProcessingToolkit
"""
文档处理工具包，用于解析、转换和操作文档内容。

支持多种文档格式（如 PDF、Word 等），提供高效的文档处理功能。
"""
