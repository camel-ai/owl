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
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from camel.messages import BaseMessage


class BaseTerminator(ABC):
    r"""Base class for terminators."""

    def __init__(self, *args, **kwargs) -> None:
        self._terminated: bool = False
        self._termination_reason: Optional[str] = None

    @abstractmethod
    def is_terminated(self, *args, **kwargs) -> Tuple[bool, Optional[str]]:
        pass

    @abstractmethod
    def reset(self):
        pass


class ResponseTerminator(BaseTerminator):
    r"""A terminator that terminates the conversation based on the response."""

    @abstractmethod
    def is_terminated(self, messages: List[BaseMessage]) -> Tuple[bool, Optional[str]]:
        pass

    @abstractmethod
    def reset(self):
        pass
