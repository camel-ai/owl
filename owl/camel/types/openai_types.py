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
# isort: skip_file
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_param import (
    ChatCompletionMessageParam,
)
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)
from openai.types.completion_usage import CompletionUsage
from openai.types.chat import ParsedChatCompletion
from openai._types import NOT_GIVEN, NotGiven
from openai.types.chat import ChatCompletionMessageToolCall

Choice = Choice
ChatCompletion = ChatCompletion
ChatCompletionChunk = ChatCompletionChunk
ChatCompletionMessage = ChatCompletionMessage
ChatCompletionMessageParam = ChatCompletionMessageParam
ChatCompletionSystemMessageParam = ChatCompletionSystemMessageParam
ChatCompletionUserMessageParam = ChatCompletionUserMessageParam
ChatCompletionAssistantMessageParam = ChatCompletionAssistantMessageParam
ChatCompletionToolMessageParam = ChatCompletionToolMessageParam
ChatCompletionMessageToolCall = ChatCompletionMessageToolCall
CompletionUsage = CompletionUsage
NOT_GIVEN = NOT_GIVEN
NotGiven = NotGiven
ParsedChatCompletion = ParsedChatCompletion
