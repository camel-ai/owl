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
# ruff: noqa: I001
from .function_tool import (
    FunctionTool,
    get_openai_function_schema,
    get_openai_tool_schema,
    generate_docstring,
)
from .open_api_specs.security_config import openapi_security_config

from .math_toolkit import MathToolkit
from .search_toolkit import SearchToolkit
from .weather_toolkit import WeatherToolkit
from .dalle_toolkit import DalleToolkit
from .ask_news_toolkit import AskNewsToolkit, AsyncAskNewsToolkit
from .linkedin_toolkit import LinkedInToolkit
from .reddit_toolkit import RedditToolkit
from .meshy_toolkit import MeshyToolkit

from .base import BaseToolkit
from .google_maps_toolkit import GoogleMapsToolkit
from .code_execution import CodeExecutionToolkit
from .github_toolkit import GithubToolkit
from .google_scholar_toolkit import GoogleScholarToolkit
from .arxiv_toolkit import ArxivToolkit
from .slack_toolkit import SlackToolkit
from .twitter_toolkit import TwitterToolkit
from .open_api_toolkit import OpenAPIToolkit
from .retrieval_toolkit import RetrievalToolkit
from .notion_toolkit import NotionToolkit
from .human_toolkit import HumanToolkit
from .audio_analysis_toolkit import AudioAnalysisToolkit
from .image_analysis_toolkit import ImageAnalysisToolkit
from .video_analysis_toolkit import VideoAnalysisToolkit
from .video_downloader_toolkit import VideoDownloaderToolkit
from .excel_toolkit import ExcelToolkit
from .document_processing_toolkit import DocumentProcessingToolkit
from .sympy_toolkit import SymPyToolkit
from .web_toolkit import WebToolkit


__all__ = [
    "BaseToolkit",
    "FunctionTool",
    "get_openai_function_schema",
    "get_openai_tool_schema",
    "generate_docstring",
    "openapi_security_config",
    "GithubToolkit",
    "MathToolkit",
    "GoogleMapsToolkit",
    "SearchToolkit",
    "SlackToolkit",
    "DalleToolkit",
    "TwitterToolkit",
    "WeatherToolkit",
    "RetrievalToolkit",
    "OpenAPIToolkit",
    "LinkedInToolkit",
    "RedditToolkit",
    "CodeExecutionToolkit",
    "AskNewsToolkit",
    "AsyncAskNewsToolkit",
    "GoogleScholarToolkit",
    "NotionToolkit",
    "ArxivToolkit",
    "HumanToolkit",
    "MeshyToolkit",
    "VideoDownloaderToolkit",
    "AudioAnalysisToolkit",
    "ImageAnalysisToolkit",
    "VideoAnalysisToolkit",
    "ExcelToolkit",
    "DocumentProcessingToolkit",
    "SymPyToolkit",
    "WebToolkit",
]
