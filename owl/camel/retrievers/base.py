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
from typing import Any, Callable

DEFAULT_TOP_K_RESULTS = 1


def _query_unimplemented(self, *input: Any) -> None:
    r"""Defines the query behavior performed at every call.

    Query the results. Subclasses should implement this
        method according to their specific needs.

    It should be overridden by all subclasses.

    .. note::
        Although the recipe for forward pass needs to be defined within
        this function, one should call the :class:`BaseRetriever` instance
        afterwards instead of this since the former takes care of running the
        registered hooks while the latter silently ignores them.
    """
    raise NotImplementedError(f"Retriever [{type(self).__name__}] is missing the required" ' "query" function')


def _process_unimplemented(self, *input: Any) -> None:
    r"""Defines the process behavior performed at every call.

    Processes content from a file or URL, divides it into chunks by
        using `Unstructured IO`,then stored internally. This method must be
        called before executing queries with the retriever.

    Should be overridden by all subclasses.

    .. note::
        Although the recipe for forward pass needs to be defined within
        this function, one should call the :class:`BaseRetriever` instance
        afterwards instead of this since the former takes care of running the
        registered hooks while the latter silently ignores them.
    """
    raise NotImplementedError(f"Retriever [{type(self).__name__}] is missing the required " '"process" function')


class BaseRetriever(ABC):
    r"""Abstract base class for implementing various types of information
    retrievers.
    """

    @abstractmethod
    def __init__(self) -> None:
        pass

    process: Callable[..., Any] = _process_unimplemented
    query: Callable[..., Any] = _query_unimplemented
