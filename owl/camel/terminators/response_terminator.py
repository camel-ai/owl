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
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from camel.messages import BaseMessage
from camel.types import TerminationMode

from .base import ResponseTerminator


class ResponseWordsTerminator(ResponseTerminator):
    r"""Terminate agent when some words reached to occurrence
    limit by any message of the response.

    Args:
        words_dict (dict): Dictionary of words and its occurrence
            threshold.
        case_sensitive (bool): Whether count the words as
            case-sensitive. (default: :obj:`False`)
        mode (TerminationMode): Whether terminate agent if any
            or all pre-set words reached the threshold.
            (default: :obj:`TerminationMode.ANY`)
    """

    def __init__(
        self,
        words_dict: Dict[str, int],
        case_sensitive: bool = False,
        mode: TerminationMode = TerminationMode.ANY,
    ):
        super().__init__()
        self.words_dict = words_dict
        self.case_sensitive = case_sensitive
        self.mode = mode
        self._word_count_dict: List[Dict[str, int]] = []
        self._validate()

    def _validate(self):
        if len(self.words_dict) == 0:
            raise ValueError("`words_dict` cannot be empty")
        for word in self.words_dict:
            threshold = self.words_dict[word]
            if threshold <= 0:
                raise ValueError(f"Threshold for word `{word}` should " f"be larger than 0, got `{threshold}`")

    def is_terminated(self, messages: List[BaseMessage]) -> Tuple[bool, Optional[str]]:
        r"""Whether terminate the agent by checking the occurrence
        of specified words reached to preset thresholds.

        Args:
            messages (list): List of :obj:`BaseMessage` from a response.

        Returns:
            tuple: A tuple containing whether the agent should be
                terminated and a string of termination reason.
        """
        if self._terminated:
            return True, self._termination_reason

        for i in range(len(messages)):
            if i >= len(self._word_count_dict):
                self._word_count_dict.append(defaultdict(int))

        for word in self.words_dict:
            special_word = word if self.case_sensitive else word.lower()
            for i, message in enumerate(messages):
                if self.case_sensitive:
                    content = message.content
                else:
                    content = message.content.lower()
                if special_word in content:
                    self._word_count_dict[i][word] += 1

        num_reached: List[int] = []
        all_reasons: List[List[str]] = []
        for i in range(len(self._word_count_dict)):
            reached = 0
            reasons: List[str] = []
            for word, value in self._word_count_dict[i].items():
                if value >= self.words_dict[word]:
                    reached += 1
                    reason = (
                        f"Word `{word}` appears {value} times in the "
                        f"{i + 1} message of the response which has "
                        f"reached termination threshold "
                        f"{self.words_dict[word]}."
                    )
                    reasons.append(reason)
            all_reasons.append(reasons)
            num_reached.append(reached)

        for i, reached in enumerate(num_reached):
            if self.mode == TerminationMode.ANY:
                if reached > 0:
                    self._terminated = True
                    self._termination_reason = "\n".join(all_reasons[i])
            elif self.mode == TerminationMode.ALL:
                if reached >= len(self.words_dict):
                    self._terminated = True
                    self._termination_reason = "\n".join(all_reasons[i])
            else:
                raise ValueError(f"Unsupported termination mode " f"`{self.mode}`")
        return self._terminated, self._termination_reason

    def reset(self):
        r"""Reset the terminator."""
        self._terminated = False
        self._termination_reason = None
        self._word_count_dict = defaultdict(int)
