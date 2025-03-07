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
from typing import Optional, Tuple

from camel.terminators.base import BaseTerminator


class TokenLimitTerminator(BaseTerminator):
    r"""Terminate agent if number of tokens reached to token limit threshold.

    Args:
        token_limit (int): Token limit threshold.
    """

    def __init__(self, token_limit: int):
        super().__init__()
        self.token_limit = token_limit

    def _validate(self):
        if self.token_limit <= 0:
            raise ValueError(f"`token_limit` should be a " f"value larger than 0, got {self.token_limit}.")

    def is_terminated(self, num_tokens: int) -> Tuple[bool, Optional[str]]:
        r"""Whether terminate the agent by checking number of
        used tokens reached to token limit.

        Args:
            num_tokens (int): Number of tokens.

        Returns:
            tuple: A tuple containing whether the agent should be
                terminated and a string of termination reason.
        """
        if self._terminated:
            return True, self._termination_reason
        if num_tokens >= self.token_limit:
            self._terminated = True
            self._termination_reason = "max_tokens_exceeded"
        return self._terminated, self._termination_reason

    def reset(self):
        r"""Reset the terminator."""
        self._terminated = False
        self._termination_reason = None
