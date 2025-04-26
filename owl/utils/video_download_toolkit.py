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

import io
import tempfile
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from PIL import Image

from camel.logger import get_logger
from camel.toolkits.base import BaseToolkit
from camel.toolkits.function_tool import FunctionTool
from camel.utils import MCPServer, dependencies_required

logger = get_logger(__name__)


def _capture_screenshot(video_file: str, timestamp: float) -> Image.Image:
    r"""Capture a screenshot from a video file at a specific timestamp.

    Args:
        video_file (str): The path to the video file.
        timestamp (float): The time in seconds from which to capture the
          screenshot.

    Returns:
        Image.Image: The captured screenshot in the form of Image.Image.
    """
    import ffmpeg

    try:
        out, _ = (
            ffmpeg.input(video_file, ss=timestamp)
            .filter('scale', 320, -1)
            .output('pipe:', vframes=1, format='image2', vcodec='png')
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to capture screenshot: {e.stderr}")

    return Image.open(io.BytesIO(out))


@MCPServer()
class VideoDownloaderToolkit(BaseToolkit):
    r"""A class for downloading videos and optionally splitting them into
    chunks.

    Args:
        download_directory (Optional[str], optional): The directory where the
            video will be downloaded to. If not provided, video will be stored
            in a temporary directory and will be cleaned up after use.
            (default: :obj:`None`)
        cookies_path (Optional[str], optional): The path to the cookies file
            for the video service in Netscape format. (default: :obj:`None`)
    """

    @dependencies_required("yt_dlp", "ffmpeg")
    def __init__(
        self,
        download_directory: Optional[str] = None,
        cookies_path: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self._cleanup = download_directory is None
        self._cookies_path = cookies_path

        self._download_directory = Path(
            download_directory or tempfile.mkdtemp()
        ).resolve()

        try:
            self._download_directory.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            raise ValueError(
                f"{self._download_directory} is not a valid directory."
            )
        except OSError as e:
            raise ValueError(
                f"Error creating directory {self._download_directory}: {e}"
            )

        logger.info(f"Video will be downloaded to {self._download_directory}")

    def __del__(self) -> None:
        r"""Deconstructor for the VideoDownloaderToolkit class.

        Cleans up the downloaded video if they are stored in a temporary
        directory.
        """
        import shutil

        if self._cleanup:
            shutil.rmtree(self._download_directory, ignore_errors=True)

    def download_video(self, url: str) -> str:
        r"""Download the video and optionally split it into chunks.

        yt-dlp will detect if the video is downloaded automatically so there
        is no need to check if the video exists.

        Returns:
            str: The path to the downloaded video file.
        """
        import yt_dlp

        video_template = self._download_directory / "%(title)s.%(ext)s"
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(video_template),
            'force_generic_extractor': True,
            'cookiefile': self._cookies_path,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download the video and get the filename
                logger.info(f"Downloading video from {url}...")
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except yt_dlp.utils.DownloadError as e:
            raise RuntimeError(f"Failed to download video from {url}: {e}")

    def get_video_bytes(
        self,
        video_path: str,
    ) -> bytes:
        r"""Download video by the path, and return the content in bytes.

        Args:
            video_path (str): The path to the video file.

        Returns:
            bytes: The video file content in bytes.
        """
        parsed_url = urlparse(video_path)
        is_url = all([parsed_url.scheme, parsed_url.netloc])
        if is_url:
            video_path = self.download_video(video_path)
        video_file = video_path

        with open(video_file, 'rb') as f:
            video_bytes = f.read()

        return video_bytes

    def get_video_screenshots(
        self, video_path: str, amount: int
    ) -> List[Image.Image]:
        r"""Capture screenshots from the video at specified timestamps or by
        dividing the video into equal parts if an integer is provided.

        Args:
            video_url (str): The URL of the video to take screenshots.
            amount (int): the amount of evenly split screenshots to capture.

        Returns:
            List[Image.Image]: A list of screenshots as Image.Image.
        """
        import ffmpeg

        parsed_url = urlparse(video_path)
        is_url = all([parsed_url.scheme, parsed_url.netloc])
        if is_url:
            video_path = self.download_video(video_path)
        video_file = video_path

        # Get the video length
        try:
            probe = ffmpeg.probe(video_file)
            video_length = float(probe['format']['duration'])
        except ffmpeg.Error as e:
            raise RuntimeError(f"Failed to determine video length: {e.stderr}")

        interval = video_length / (amount + 1)
        timestamps = [i * interval for i in range(1, amount + 1)]

        images = [_capture_screenshot(video_file, ts) for ts in timestamps]

        return images

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects representing
                the functions in the toolkit.
        """
        return [
            FunctionTool(self.download_video),
            FunctionTool(self.get_video_bytes),
            FunctionTool(self.get_video_screenshots),
        ]
