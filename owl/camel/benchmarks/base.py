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

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from camel.agents import ChatAgent

logger = logging.getLogger(__name__)


class BaseBenchmark(ABC):
    r"""Base class for benchmarks.

    Attributes:
        name (str): Name of the benchmark.
        data_dir (str): Path to the data directory.
        save_to (str): Path to save the results.
        processes (int): Number of processes to use for parallel
            processing. :(default: :obj:`1`)
    """

    def __init__(self, name: str, data_dir: str, save_to: str, processes: int = 1):
        r"""Initialize the benchmark.

        Args:
            name (str): Name of the benchmark.
            data_dir (str): Path to the data directory.
            save_to (str): Path to save the results.
            processes (int): Number of processes to use for parallel
                processing. :(default: :obj:`1`)

        """
        self.name = name
        self.data_dir = Path(data_dir)
        self.processes = processes
        self.save_to = save_to
        if not self.data_dir.exists():
            logger.info(f"Data directory {data_dir} does not exist. Creating it.")
            self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.data_dir.is_dir():
            raise NotADirectoryError(f"Data directory {data_dir} is not a directory")
        self._data: Dict[str, List[Dict[str, Any]]] = dict()
        self._results: List[Dict[str, Any]] = []

    @abstractmethod
    def download(self) -> "BaseBenchmark":
        r"""Download the benchmark data.

        Returns:
            BaseBenchmark: The benchmark instance.
        """
        pass

    @abstractmethod
    def load(self, force_download: bool = False) -> "BaseBenchmark":
        r"""Load the benchmark data.

        Args:
            force_download (bool): Whether to force download the data.

        Returns:
            BaseBenchmark: The benchmark instance.
        """
        pass

    @property
    def train(self) -> List[Dict[str, Any]]:
        r"""Get the training data.

        Returns:
            List[Dict[str, Any]]: The training data.
        """
        if not self._data:
            logger.info("Data not loaded. Loading data.")
            self.load()
        return self._data["train"]

    @property
    def valid(self) -> List[Dict[str, Any]]:
        r"""Get the validation data.

        Returns:
            List[Dict[str, Any]]: The validation data.
        """
        if not self._data:
            logger.info("Data not loaded. Loading data.")
            self.load()
        return self._data["valid"]

    @property
    def test(self) -> List[Dict[str, Any]]:
        r"""Get the test data.

        Returns:
            List[Dict[str, Any]]: The test data.
        """
        if not self._data:
            logger.info("Data not loaded. Loading data.")
            self.load()
        return self._data["test"]

    @abstractmethod
    def run(
        self,
        agent: ChatAgent,
        on: Literal["train", "valid", "test"],
        randomize: bool = False,
        subset: Optional[int] = None,
        *args,
        **kwargs,
    ) -> "BaseBenchmark":
        r"""Run the benchmark.

        Args:
            agent (ChatAgent): The chat agent.
            on (str): The data split to run the benchmark on.
            randomize (bool): Whether to randomize the data.
            subset (int): The subset of the data to run the benchmark on.

        Returns:
            BaseBenchmark: The benchmark instance.
        """
        pass

    @property
    def results(self) -> List[Dict[str, Any]]:
        r"""Get the results.

        Returns:
            List[Dict[str, Any]]: The results.
        """
        return self._results
