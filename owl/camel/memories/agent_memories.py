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

from typing import List, Optional

from camel.memories.base import AgentMemory, BaseContextCreator
from camel.memories.blocks import ChatHistoryBlock, VectorDBBlock
from camel.memories.records import ContextRecord, MemoryRecord
from camel.storages import BaseKeyValueStorage, BaseVectorStorage
from camel.types import OpenAIBackendRole


class ChatHistoryMemory(AgentMemory):
    r"""An agent memory wrapper of :obj:`ChatHistoryBlock`.

    Args:
        context_creator (BaseContextCreator): A model context creator.
        storage (BaseKeyValueStorage, optional): A storage backend for storing
            chat history. If `None`, an :obj:`InMemoryKeyValueStorage`
            will be used. (default: :obj:`None`)
        window_size (int, optional): The number of recent chat messages to
            retrieve. If not provided, the entire chat history will be
            retrieved.  (default: :obj:`None`)
    """

    def __init__(
        self,
        context_creator: BaseContextCreator,
        storage: Optional[BaseKeyValueStorage] = None,
        window_size: Optional[int] = None,
    ) -> None:
        if window_size is not None and not isinstance(window_size, int):
            raise TypeError("`window_size` must be an integer or None.")
        if window_size is not None and window_size < 0:
            raise ValueError("`window_size` must be non-negative.")
        self._context_creator = context_creator
        self._window_size = window_size
        self._chat_history_block = ChatHistoryBlock(storage=storage)

    def retrieve(self) -> List[ContextRecord]:
        return self._chat_history_block.retrieve(self._window_size)

    def write_records(self, records: List[MemoryRecord]) -> None:
        self._chat_history_block.write_records(records)

    def get_context_creator(self) -> BaseContextCreator:
        return self._context_creator

    def clear(self) -> None:
        self._chat_history_block.clear()


class VectorDBMemory(AgentMemory):
    r"""An agent memory wrapper of :obj:`VectorDBBlock`. This memory queries
    messages stored in the vector database. Notice that the most recent
    messages will not be added to the context.

    Args:
        context_creator (BaseContextCreator): A model context creator.
        storage (BaseVectorStorage, optional): A vector storage storage. If
            `None`, an :obj:`QdrantStorage` will be used.
            (default: :obj:`None`)
        retrieve_limit (int, optional): The maximum number of messages
            to be added into the context.  (default: :obj:`3`)
    """

    def __init__(
        self,
        context_creator: BaseContextCreator,
        storage: Optional[BaseVectorStorage] = None,
        retrieve_limit: int = 3,
    ) -> None:
        self._context_creator = context_creator
        self._retrieve_limit = retrieve_limit
        self._vectordb_block = VectorDBBlock(storage=storage)

        self._current_topic: str = ""

    def retrieve(self) -> List[ContextRecord]:
        return self._vectordb_block.retrieve(
            self._current_topic,
            limit=self._retrieve_limit,
        )

    def write_records(self, records: List[MemoryRecord]) -> None:
        # Assume the last user input is the current topic.
        for record in records:
            if record.role_at_backend == OpenAIBackendRole.USER:
                self._current_topic = record.message.content
        self._vectordb_block.write_records(records)

    def get_context_creator(self) -> BaseContextCreator:
        return self._context_creator


class LongtermAgentMemory(AgentMemory):
    r"""An implementation of the :obj:`AgentMemory` abstract base class for
    augmenting ChatHistoryMemory with VectorDBMemory.

    Args:
        context_creator (BaseContextCreator): A model context creator.
        chat_history_block (Optional[ChatHistoryBlock], optional): A chat
            history block. If `None`, a :obj:`ChatHistoryBlock` will be used.
            (default: :obj:`None`)
        vector_db_block (Optional[VectorDBBlock], optional): A vector database
            block. If `None`, a :obj:`VectorDBBlock` will be used.
            (default: :obj:`None`)
        retrieve_limit (int, optional): The maximum number of messages
            to be added into the context.  (default: :obj:`3`)
    """

    def __init__(
        self,
        context_creator: BaseContextCreator,
        chat_history_block: Optional[ChatHistoryBlock] = None,
        vector_db_block: Optional[VectorDBBlock] = None,
        retrieve_limit: int = 3,
    ) -> None:
        self.chat_history_block = chat_history_block or ChatHistoryBlock()
        self.vector_db_block = vector_db_block or VectorDBBlock()
        self.retrieve_limit = retrieve_limit
        self._context_creator = context_creator
        self._current_topic: str = ""

    def get_context_creator(self) -> BaseContextCreator:
        r"""Returns the context creator used by the memory.

        Returns:
            BaseContextCreator: The context creator used by the memory.
        """
        return self._context_creator

    def retrieve(self) -> List[ContextRecord]:
        r"""Retrieves context records from both the chat history and the vector
        database.

        Returns:
            List[ContextRecord]: A list of context records retrieved from both
                the chat history and the vector database.
        """
        chat_history = self.chat_history_block.retrieve()
        vector_db_retrieve = self.vector_db_block.retrieve(self._current_topic, self.retrieve_limit)
        return chat_history[:1] + vector_db_retrieve + chat_history[1:]

    def write_records(self, records: List[MemoryRecord]) -> None:
        r"""Converts the provided chat messages into vector representations and
        writes them to the vector database.

        Args:
            records (List[MemoryRecord]): Messages to be added to the vector
                database.
        """
        self.vector_db_block.write_records(records)
        self.chat_history_block.write_records(records)

        for record in records:
            if record.role_at_backend == OpenAIBackendRole.USER:
                self._current_topic = record.message.content

    def clear(self) -> None:
        r"""Removes all records from the memory."""
        self.chat_history_block.clear()
        self.vector_db_block.clear()
