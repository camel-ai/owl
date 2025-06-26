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

import tempfile
from pathlib import Path
from typing import List, Optional

import ffmpeg
from PIL import Image
from scenedetect import (  # type: ignore[import-untyped]
    SceneManager,
    VideoManager,
)
from scenedetect.detectors import (  # type: ignore[import-untyped]
    ContentDetector,
)

from camel.agents import ChatAgent
from camel.configs import QwenConfig
from camel.messages import BaseMessage
from camel.models import ModelFactory, OpenAIAudioModels
from camel.toolkits.base import BaseToolkit
from camel.toolkits.function_tool import FunctionTool
from camel.types import ModelPlatformType, ModelType
from camel.utils import dependencies_required
from loguru import logger

from .video_download_toolkit import (
    VideoDownloaderToolkit,
    _capture_screenshot,
)

import os


class VideoAnalysisToolkit(BaseToolkit):
    
    
    def __init__(self, download_directory: Optional[str] = None):
        self.video_downloader_toolkit = VideoDownloaderToolkit(download_directory=download_directory)
    
    
    def ask_question_about_video(self, video_path: str, question: str) -> str:
        r"""Ask a question about the video.
        
        Args:
            video_path (str): The path to the video file.
            question (str): The question to ask about the video.

        Returns:
            str: The answer to the question.
        """
        os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')
        
        import pathlib
        from google import genai
        from google.genai import types
        
        client = genai.Client()

        model = 'models/gemini-2.0-flash'

        response = client.models.generate_content(
            model=model,
            contents=types.Content(
                parts=[
                    types.Part(text=question),
                    types.Part(file_data=types.FileData(file_uri=video_path))
                ]
            )
        )

        logger.debug(f"Video analysis response from gemini: {response.text}")
        return response.text
    
        
    def get_tools(self) -> List[FunctionTool]:
        """
        Get the tools in the toolkit.
        """
        return [FunctionTool(self.ask_question_about_video)]
    

