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
import warnings
from typing import List, Optional

from camel.memories.base import MemoryBlock
from camel.memories.records import ContextRecord, MemoryRecord
from camel.storages import BaseKeyValueStorage, InMemoryKeyValueStorage
from camel.types import OpenAIBackendRole


class ChatHistoryBlock(MemoryBlock):
    r"""An implementation of the :obj:`MemoryBlock` abstract base class for
    maintaining a record of chat histories.

    This memory block helps manage conversation histories with a key-value
    storage backend, either provided by the user or using a default
    in-memory storage. It offers a windowed approach to retrieving chat
    histories, allowing users to specify how many recent messages they'd
    like to fetch.

    Args:
        storage (BaseKeyValueStorage, optional): A storage mechanism for
            storing chat history. If `None`, an :obj:`InMemoryKeyValueStorage`
            will be used. (default: :obj:`None`)
        keep_rate (float, optional): In historical messages, the score of the
            last message is 1.0, and with each step taken backward, the score
            of the message is multiplied by the `keep_rate`. Higher `keep_rate`
            leads to high possiblity to keep history messages during context
            creation.
    """

    def __init__(
        self,
        storage: Optional[BaseKeyValueStorage] = None,
        keep_rate: float = 0.9,
    ) -> None:
        if keep_rate > 1 or keep_rate < 0:
            raise ValueError("`keep_rate` should be in [0,1]")
        self.storage = storage or InMemoryKeyValueStorage()
        self.keep_rate = keep_rate

    def retrieve(
        self,
        window_size: Optional[int] = None,
    ) -> List[ContextRecord]:
        r"""Retrieves records with a proper size for the agent from the memory
        based on the window size or fetches the entire chat history if no
        window size is specified.

        Args:
            window_size (int, optional): Specifies the number of recent chat
                messages to retrieve. If not provided, the entire chat history
                will be retrieved. (default: :obj:`None`)

        Returns:
            List[ContextRecord]: A list of retrieved records.
        """
        record_dicts = self.storage.load()
        if len(record_dicts) == 0:
            warnings.warn("The `ChatHistoryMemory` is empty.")
            return list()

        chat_records: List[MemoryRecord] = []
        truncate_idx = -window_size if window_size is not None else 0
        for record_dict in record_dicts[truncate_idx:]:
            chat_records.append(MemoryRecord.from_dict(record_dict))

        # We assume that, in the chat history memory, the closer the record is
        # to the current message, the more score it will be.
        output_records = []
        score = 1.0
        for record in reversed(chat_records):
            if record.role_at_backend == OpenAIBackendRole.SYSTEM:
                # System messages are always kept.
                output_records.append(ContextRecord(memory_record=record, score=1.0))
            else:
                # Other messages' score drops down gradually
                score *= self.keep_rate
                output_records.append(ContextRecord(memory_record=record, score=score))

        output_records.reverse()
        return output_records

    def write_records(self, records: List[MemoryRecord]) -> None:
        r"""Writes memory records to the memory. Additionally, performs
        validation checks on the messages.

        Args:
            records (List[MemoryRecord]): Memory records to be added to the
                memory.
        """
        stored_records = []
        for record in records:
            stored_records.append(record.to_dict())
        self.storage.save(stored_records)

    def clear(self) -> None:
        r"""Clears all chat messages from the memory."""
        self.storage.clear()
