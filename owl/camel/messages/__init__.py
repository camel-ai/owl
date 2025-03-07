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
from typing import Union

from camel.types import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

from .conversion import (
    AlpacaItem,
    HermesFunctionFormatter,
    ShareGPTMessage,
)
from .conversion.conversation_models import (
    ShareGPTConversation,
)
from .conversion.sharegpt.function_call_formatter import (
    FunctionCallFormatter,
)

OpenAISystemMessage = ChatCompletionSystemMessageParam
OpenAIAssistantMessage = Union[
    ChatCompletionAssistantMessageParam,
    ChatCompletionToolMessageParam,
]
OpenAIUserMessage = ChatCompletionUserMessageParam
OpenAIToolMessageParam = ChatCompletionToolMessageParam

OpenAIMessage = ChatCompletionMessageParam


from .base import BaseMessage  # noqa: E402
from .func_message import FunctionCallingMessage  # noqa: E402

__all__ = [
    "OpenAISystemMessage",
    "OpenAIAssistantMessage",
    "OpenAIUserMessage",
    "OpenAIToolMessageParam",
    "OpenAIMessage",
    "FunctionCallFormatter",
    "HermesFunctionFormatter",
    "ShareGPTConversation",
    "ShareGPTMessage",
    "BaseMessage",
    "FunctionCallingMessage",
    "AlpacaItem",
]
