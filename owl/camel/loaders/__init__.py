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

from .apify_reader import Apify
from .base_io import File
from .chunkr_reader import ChunkrReader
from .firecrawl_reader import Firecrawl
from .jina_url_reader import JinaURLReader
from .unstructured_io import UnstructuredIO

__all__ = [
    "File",
    "UnstructuredIO",
    "JinaURLReader",
    "Firecrawl",
    "Apify",
    "ChunkrReader",
]
