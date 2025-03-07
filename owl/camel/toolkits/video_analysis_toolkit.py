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

from .video_downloader_toolkit import (
    VideoDownloaderToolkit,
    _capture_screenshot,
)

logger = logging.getLogger(__name__)

VIDEO_QA_PROMPT = """
Analyze the provided video frames and corresponding audio transcription to \
answer the given question(s) thoroughly and accurately.

Instructions:
    1. Visual Analysis:
        - Examine the video frames to identify visible entities.
        - Differentiate objects, species, or features based on key attributes \
such as size, color, shape, texture, or behavior.
        - Note significant groupings, interactions, or contextual patterns \
relevant to the analysis.

    2. Audio Integration:
        - Use the audio transcription to complement or clarify your visual \
observations.
        - Identify names, descriptions, or contextual hints in the \
transcription that help confirm or refine your visual analysis.

    3. Detailed Reasoning and Justification:
        - Provide a brief explanation of how you identified and distinguished \
each species or object.
        - Highlight specific features or contextual clues that informed \
your reasoning.

    4. Comprehensive Answer:
        - Specify the total number of distinct species or object types \
identified in the video.
        - Describe the defining characteristics and any supporting evidence \
from the video and transcription.

    5. Important Considerations:
        - Pay close attention to subtle differences that could distinguish \
similar-looking species or objects 
          (e.g., juveniles vs. adults, closely related species).
        - Provide concise yet complete explanations to ensure clarity.

**Audio Transcription:**
{audio_transcription}

**Question:**
{question}
"""


class VideoAnalysisToolkit(BaseToolkit):
    r"""A class for analysing videos with vision-language model.

    Args:
        download_directory (Optional[str], optional): The directory where the
            video will be downloaded to. If not provided, video will be stored
            in a temporary directory and will be cleaned up after use.
            (default: :obj:`None`)
    """

    @dependencies_required("ffmpeg", "scenedetect")
    def __init__(
        self,
        download_directory: Optional[str] = None,
    ) -> None:
        self._cleanup = download_directory is None

        self._download_directory = Path(download_directory or tempfile.mkdtemp()).resolve()

        self.video_downloader_toolkit = VideoDownloaderToolkit(download_directory=str(self._download_directory))

        try:
            self._download_directory.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            raise ValueError(f"{self._download_directory} is not a valid directory.")
        except OSError as e:
            raise ValueError(f"Error creating directory {self._download_directory}: {e}")

        logger.info(f"Video will be downloaded to {self._download_directory}")

        self.vl_model = ModelFactory.create(
            model_platform=ModelPlatformType.QWEN,
            model_type=ModelType.QWEN_VL_MAX,
            model_config_dict=QwenConfig(temperature=0.2).as_dict(),
        )

        self.vl_agent = ChatAgent(model=self.vl_model, output_language="English")

        self.audio_models = OpenAIAudioModels()

    def _extract_audio_from_video(self, video_path: str, output_format: str = "mp3") -> str:
        r"""Extract audio from the video.

        Args:
            video_path (str): The path to the video file.
            output_format (str): The format of the audio file to be saved.
                (default: :obj:`"mp3"`)

        Returns:
            str: The path to the audio file."""

        output_path = video_path.rsplit(".", 1)[0] + f".{output_format}"
        try:
            (ffmpeg.input(video_path).output(output_path, vn=None, acodec="libmp3lame").run())
            return output_path
        except ffmpeg.Error as e:
            raise RuntimeError(f"FFmpeg-Python failed: {e}")

    def _transcribe_audio(self, audio_path: str) -> str:
        r"""Transcribe the audio of the video."""
        audio_transcript = self.audio_models.speech_to_text(audio_path)
        return audio_transcript

    def _extract_keyframes(self, video_path: str, num_frames: int, threshold: float = 25.0) -> List[Image.Image]:
        r"""Extract keyframes from a video based on scene changes
        and return them as PIL.Image.Image objects.

        Args:
            video_path (str): Path to the video file.
            num_frames (int): Number of keyframes to extract.
            threshold (float): The threshold value for scene change detection.

        Returns:
            list: A list of PIL.Image.Image objects representing
                the extracted keyframes.
        """
        video_manager = VideoManager([video_path])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))

        video_manager.set_duration()
        video_manager.start()
        scene_manager.detect_scenes(video_manager)

        scenes = scene_manager.get_scene_list()
        keyframes: List[Image.Image] = []

        for start_time, _ in scenes:
            if len(keyframes) >= num_frames:
                break
            frame = _capture_screenshot(video_path, start_time)
            keyframes.append(frame)

        print(len(keyframes))
        return keyframes

    def ask_question_about_video(
        self,
        video_path: str,
        question: str,
        num_frames: int = 28,
        # 28 is the maximum number of frames
        # that can be displayed in a single message for
        # the Qwen-VL-Max model
    ) -> str:
        r"""Ask a question about the video.

        Args:
            video_path (str): The path to the video file.
                It can be a local file or a URL (such as Youtube website).
            question (str): The question to ask about the video.
            num_frames (int): The number of frames to extract from the video.
                To be adjusted based on the length of the video.
                (default: :obj:`28`)

        Returns:
            str: The answer to the question.
        """

        from urllib.parse import urlparse

        parsed_url = urlparse(video_path)
        is_url = all([parsed_url.scheme, parsed_url.netloc])

        if is_url:
            video_path = self.video_downloader_toolkit.download_video(video_path)
        audio_path = self._extract_audio_from_video(video_path)

        video_frames = self._extract_keyframes(video_path, num_frames)

        audio_transcript = self._transcribe_audio(audio_path)

        prompt = VIDEO_QA_PROMPT.format(
            audio_transcription=audio_transcript,
            question=question,
        )

        print(prompt)

        msg = BaseMessage.make_user_message(
            role_name="User",
            content=prompt,
            image_list=video_frames,
        )

        response = self.vl_agent.step(msg)
        answer = response.msgs[0].content

        return answer

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects representing
                the functions in the toolkit.
        """
        return [FunctionTool(self.ask_question_about_video)]
