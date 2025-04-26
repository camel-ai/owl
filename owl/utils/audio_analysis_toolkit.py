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
import os
import uuid
from typing import List, Optional
from urllib.parse import urlparse

import requests

from camel.logger import get_logger
from camel.messages import BaseMessage
from camel.models import BaseAudioModel, BaseModelBackend, OpenAIAudioModels
from camel.toolkits.base import BaseToolkit
from camel.toolkits.function_tool import FunctionTool
from camel.utils import MCPServer

from llm_related_config import USE_SEW_PROMPT, INDEX, FILE_NAME


logger = get_logger(__name__)


file_path = FILE_NAME  # Corrected spelling from "promt" to "prompt"
try:
    import json
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)
    print(data_list)
except FileNotFoundError:
    logger.warning(f"Prompt file {file_path} not found, using default settings")
    data_list = []  # Default empty list if file doesn't exist

selected_prompt = data_list[INDEX]
Audio_analysis_prompt = selected_prompt['Audio_analysis_prompt']

def download_file(url: str, cache_dir: str) -> str:
    r"""Download a file from a URL to a local cache directory.

    Args:
        url (str): The URL of the file to download.
        cache_dir (str): The directory to save the downloaded file.

    Returns:
        str: The path to the downloaded file.

    Raises:
        Exception: If the download fails.
    """
    # Create cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)

    # Extract filename from URL or generate a unique one
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename:
        # Generate a unique filename if none is provided in the URL
        file_ext = ".mp3"  # Default extension
        content_type = None

        # Try to get the file extension from the content type
        try:
            response = requests.head(url)
            content_type = response.headers.get('Content-Type', '')
            if 'audio/wav' in content_type:
                file_ext = '.wav'
            elif 'audio/mpeg' in content_type:
                file_ext = '.mp3'
            elif 'audio/ogg' in content_type:
                file_ext = '.ogg'
        except Exception:
            pass

        filename = f"{uuid.uuid4()}{file_ext}"

    local_path = os.path.join(cache_dir, filename)

    # Download the file
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    logger.debug(f"Downloaded file from {url} to {local_path}")
    return local_path


@MCPServer()
class AudioAnalysisToolkit(BaseToolkit):
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        transcribe_model: Optional[BaseAudioModel] = None,
        audio_reasoning_model: Optional[BaseModelBackend] = None,
        timeout: Optional[float] = None,
    ):
        r"""A toolkit for audio processing and analysis. This class provides
        methods for processing, transcribing, and extracting information from
        audio data, including direct question answering about audio content.

        Args:
            cache_dir (Optional[str]): Directory path for caching downloaded
                audio files. If not provided, 'tmp/' will be used.
                (default: :obj:`None`)
            transcribe_model (Optional[BaseAudioModel]): Model used for audio
                transcription. If not provided, OpenAIAudioModels will be used.
                (default: :obj:`None`)
            audio_reasoning_model (Optional[BaseModelBackend]): Model used for
                audio reasoning and question answering.
                If not provided, uses the default model from ChatAgent.
                (default: :obj:`None`)
            timeout (Optional[float]): The timeout value for API requests
                    in seconds. If None, no timeout is applied.
                    (default: :obj:`None`)
        """
        super().__init__(timeout=timeout)
        self.cache_dir = 'tmp/'
        if cache_dir:
            self.cache_dir = cache_dir

        if transcribe_model:
            self.transcribe_model = transcribe_model
        else:
            self.transcribe_model = OpenAIAudioModels()
            logger.warning(
                "No audio transcription model provided. "
                "Using OpenAIAudioModels."
            )

        from camel.agents import ChatAgent

        if audio_reasoning_model:
            self.audio_agent = ChatAgent(model=audio_reasoning_model)
        else:
            self.audio_agent = ChatAgent()
            logger.warning(
                "No audio reasoning model provided. Using default model in"
                " ChatAgent."
            )

    def audio2text(self, audio_path: str) -> str:
        r"""Transcribe audio to text.

        Args:
            audio_path (str): The path to the audio file or URL.

        Returns:
            str: The transcribed text.
        """
        logger.debug(
            f"Calling transcribe_audio method for audio file `{audio_path}`."
        )

        try:
            audio_transcript = self.transcribe_model.speech_to_text(audio_path)
            if not audio_transcript:
                logger.warning("Audio transcription returned empty result")
                return "No audio transcription available."
            return audio_transcript
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return "Audio transcription failed."

    def ask_question_about_audio(self, audio_path: str, question: str) -> str:
        r"""Ask any question about the audio and get the answer using
        multimodal model.

        Args:
            audio_path (str): The path to the audio file.
            question (str): The question to ask about the audio.

        Returns:
            str: The answer to the question.
        """

        logger.debug(
            f"Calling ask_question_about_audio method for audio file \
            `{audio_path}` and question `{question}`."
        )

        parsed_url = urlparse(audio_path)
        is_url = all([parsed_url.scheme, parsed_url.netloc])
        local_audio_path = audio_path

        # If the audio is a URL, download it first
        if is_url:
            try:
                local_audio_path = download_file(audio_path, self.cache_dir)
            except Exception as e:
                logger.error(f"Failed to download audio file: {e}")
                return f"Failed to download audio file: {e!s}"

        # Try direct audio question answering first
        try:
            # Check if the transcribe_model supports audio_question_answering
            if hasattr(self.transcribe_model, 'audio_question_answering'):
                logger.debug("Using direct audio question answering")
                response = self.transcribe_model.audio_question_answering(
                    local_audio_path, question
                )
                return response
        except Exception as e:
            logger.warning(
                f"Direct audio question answering failed: {e}. "
                "Falling back to transcription-based approach."
            )

        # Fallback to transcription-based approach
        try:
            transcript = self.audio2text(local_audio_path)
            reasoning_prompt = f"""
            <speech_transcription_result>{transcript}</
            speech_transcription_result>

            Please answer the following question based on the speech 
            transcription result above:
            <question>{question}</question>
            """
            if USE_SEW_PROMPT:
                reasoning_prompt = Audio_analysis_prompt
                reasoning_prompt  = f"""
            <speech_transcription_result>{transcript}</
            speech_transcription_result>

            """ + reasoning_prompt + """

            <question>{question}</question>
            """
                
            msg = BaseMessage.make_user_message(
                role_name="User", content=reasoning_prompt
            )
            response = self.audio_agent.step(msg)

            if not response or not response.msgs:
                logger.error("Model returned empty response")
                return (
                    "Failed to generate an answer. "
                    "The model returned an empty response."
                )

            answer = response.msgs[0].content
            return answer
        except Exception as e:
            logger.error(f"Audio question answering failed: {e}")
            return f"Failed to answer question about audio: {e!s}"

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the functions
            in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects representing the
                functions in the toolkit.
        """
        return [
            FunctionTool(self.ask_question_about_audio),
            FunctionTool(self.audio2text),
        ]
