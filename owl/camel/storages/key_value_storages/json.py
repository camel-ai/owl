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

import json
from enum import EnumMeta
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

from camel.storages.key_value_storages import BaseKeyValueStorage
from camel.types import (
    ModelType,
    OpenAIBackendRole,
    RoleType,
    TaskType,
)


class _CamelJSONEncoder(json.JSONEncoder):
    r"""A custom JSON encoder for serializing specifically enumerated types.
    Ensures enumerated types can be stored in and retrieved from JSON format.
    """

    CAMEL_ENUMS: ClassVar[Dict[str, EnumMeta]] = {
        "RoleType": RoleType,
        "TaskType": TaskType,
        "ModelType": ModelType,
        "OpenAIBackendRole": OpenAIBackendRole,
    }

    def default(self, obj) -> Any:
        if type(obj) in self.CAMEL_ENUMS.values():
            return {"__enum__": str(obj)}
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class JsonStorage(BaseKeyValueStorage):
    r"""A concrete implementation of the :obj:`BaseKeyValueStorage` using JSON
    files. Allows for persistent storage of records in a human-readable format.

    Args:
        path (Path, optional): Path to the desired JSON file. If `None`, a
            default path `./chat_history.json` will be used.
            (default: :obj:`None`)
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self.json_path = path or Path("./chat_history.json")
        self.json_path.touch()

    def _json_object_hook(self, d) -> Any:
        if "__enum__" in d:
            name, member = d["__enum__"].split(".")
            return getattr(_CamelJSONEncoder.CAMEL_ENUMS[name], member)
        else:
            return d

    def save(self, records: List[Dict[str, Any]]) -> None:
        r"""Saves a batch of records to the key-value storage system.

        Args:
            records (List[Dict[str, Any]]): A list of dictionaries, where each
                dictionary represents a unique record to be stored.
        """
        with self.json_path.open("a") as f:
            f.writelines([json.dumps(r, cls=_CamelJSONEncoder) + "\n" for r in records])

    def load(self) -> List[Dict[str, Any]]:
        r"""Loads all stored records from the key-value storage system.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                represents a stored record.
        """
        with self.json_path.open("r") as f:
            return [json.loads(r, object_hook=self._json_object_hook) for r in f.readlines()]

    def clear(self) -> None:
        r"""Removes all records from the key-value storage system."""
        with self.json_path.open("w"):
            pass
