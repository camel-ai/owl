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
import asyncio
from copy import deepcopy

from camel.toolkits import FunctionTool


def sync_funcs_to_async(funcs: list[FunctionTool]) -> list[FunctionTool]:
    r"""Convert a list of Python synchronous functions to Python
    asynchronous functions.

    Args:
        funcs (list[FunctionTool]): List of Python synchronous
            functions in the :obj:`FunctionTool` format.

    Returns:
        list[FunctionTool]: List of Python asynchronous functions
            in the :obj:`FunctionTool` format.
    """
    async_funcs = []
    for func in funcs:
        sync_func = func.func

        def async_callable(*args, **kwargs):
            return asyncio.to_thread(sync_func, *args, **kwargs)  # noqa: B023

        async_funcs.append(FunctionTool(async_callable, deepcopy(func.openai_tool_schema)))
    return async_funcs
