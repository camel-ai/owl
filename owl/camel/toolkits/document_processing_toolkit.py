from camel.loaders.chunkr_reader import ChunkrReader
from camel.toolkits.base import BaseToolkit
from camel.toolkits.function_tool import FunctionTool
from camel.toolkits import ImageAnalysisToolkit, AudioAnalysisToolkit, VideoAnalysisToolkit, ExcelToolkit
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelType
from camel.models import OpenAIModel, DeepSeekModel
from docx2markdown._docx_to_markdown import docx_to_markdown
from chunkr_ai import Chunkr
import openai
import requests
import mimetypes
import json
from retry import retry
from typing import List, Dict, Any, Optional, Tuple, Literal
from PIL import Image
from io import BytesIO
from loguru import logger
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urlparse, urljoin
import os
import subprocess
import xmltodict
import asyncio
import nest_asyncio

nest_asyncio.apply()


class DocumentProcessingToolkit(BaseToolkit):
    r"""A class representing a toolkit for processing document and return the content of the document.

    This class provides method for processing docx, pdf, pptx, etc. It cannot process excel files.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.image_tool = ImageAnalysisToolkit()
        self.audio_tool = AudioAnalysisToolkit()
        self.excel_tool = ExcelToolkit()

        self.cache_dir = "tmp/"
        if cache_dir:
            self.cache_dir = cache_dir

    @retry((requests.RequestException))
    def extract_document_content(self, document_path: str) -> Tuple[bool, str]:
        r"""Extract the content of a given document (or url) and return the processed text.
        It may filter out some information, resulting in inaccurate content.

        Args:
            document_path (str): The path of the document to be processed, either a local path or a URL. It can process image, audio files, zip files and webpages, etc.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating whether the document was processed successfully, and the content of the document (if success).
        """
        logger.debug(f"Calling extract_document_content function with document_path=`{document_path}`")

        if any(document_path.endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
            res = self.image_tool.ask_question_about_image(
                document_path, "Please make a detailed caption about the image."
            )
            return True, res

        if any(document_path.endswith(ext) for ext in [".mp3", ".wav"]):
            res = self.audio_tool.ask_question_about_audio(
                document_path, "Please transcribe the audio content to text."
            )
            return True, res

        if any(document_path.endswith(ext) for ext in ["xls", "xlsx"]):
            res = self.excel_tool.extract_excel_content(document_path)
            return True, res

        if any(document_path.endswith(ext) for ext in ["zip"]):
            extracted_files = self._unzip_file(document_path)
            return True, f"The extracted files are: {extracted_files}"

        if any(document_path.endswith(ext) for ext in ["json", "jsonl", "jsonld"]):
            with open(document_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            f.close()
            return True, content

        if any(document_path.endswith(ext) for ext in ["py"]):
            with open(document_path, "r", encoding="utf-8") as f:
                content = f.read()
            f.close()
            return True, content

        if any(document_path.endswith(ext) for ext in ["xml"]):
            data = None
            with open(document_path, "r", encoding="utf-8") as f:
                content = f.read()
            f.close()

            try:
                data = xmltodict.parse(content)
                logger.debug(f"The extracted xml data is: {data}")
                return True, data

            except Exception as e:
                logger.debug(f"The raw xml data is: {content}")
                return True, content

        if self._is_webpage(document_path):
            extracted_text = self._extract_webpage_content(document_path)
            return True, extracted_text

        else:
            # judge if url
            parsed_url = urlparse(document_path)
            is_url = all([parsed_url.scheme, parsed_url.netloc])
            if not is_url:
                if not os.path.exists(document_path):
                    return f"Document not found at path: {document_path}."

            # if is docx file, use docx2markdown to convert it
            if document_path.endswith(".docx"):
                if is_url:
                    tmp_path = self._download_file(document_path)
                else:
                    tmp_path = document_path

                file_name = os.path.basename(tmp_path)
                md_file_path = f"{file_name}.md"
                docx_to_markdown(tmp_path, md_file_path)

                # load content of md file
                with open(md_file_path, "r") as f:
                    extracted_text = f.read()
                f.close()
                return True, extracted_text
            try:
                # result = asyncio.run(self._extract_content_with_chunkr(document_path))
                raise ValueError("Chunkr is not available.")
                return True, result

            except Exception as e:
                logger.warning(f"Error occurred while using chunkr to process document: {e}")
                if document_path.endswith(".pdf"):
                    # try using pypdf to extract text from pdf
                    try:
                        from PyPDF2 import PdfReader

                        if is_url:
                            tmp_path = self._download_file(document_path)
                            document_path = tmp_path

                        with open(document_path, "rb") as f:
                            reader = PdfReader(f)
                            extracted_text = ""
                            for page in reader.pages:
                                extracted_text += page.extract_text()

                        return True, extracted_text

                    except Exception as e:
                        logger.error(f"Error occurred while processing pdf: {e}")
                        return False, f"Error occurred while processing pdf: {e}"

                logger.error(f"Error occurred while processing document: {e}")
                return False, f"Error occurred while processing document: {e}"

    def _is_webpage(self, url: str) -> bool:
        r"""Judge whether the given URL is a webpage."""
        try:
            parsed_url = urlparse(url)
            is_url = all([parsed_url.scheme, parsed_url.netloc])
            if not is_url:
                return False

            path = parsed_url.path
            file_type, _ = mimetypes.guess_type(path)
            if "text/html" in file_type:
                return True

            response = requests.head(url, allow_redirects=True, timeout=10)
            content_type = response.headers.get("Content-Type", "").lower()

            if "text/html" in content_type:
                return True
            else:
                return False

        except requests.exceptions.RequestException as e:
            # raise RuntimeError(f"Error while checking the URL: {e}")
            logger.warning(f"Error while checking the URL: {e}")
            return False

        except TypeError:
            return True

    @retry(requests.RequestException)
    async def _extract_content_with_chunkr(
        self, document_path: str, output_format: Literal["json", "markdown"] = "markdown"
    ) -> str:

        chunkr = Chunkr(api_key=os.getenv("CHUNKR_API_KEY"))

        result = await chunkr.upload(document_path)

        # result = chunkr.upload(document_path)

        if result.status == "Failed":
            logger.error(f"Error while processing document {document_path}: {result.message}")
            return f"Error while processing document: {result.message}"

        # extract document name
        document_name = os.path.basename(document_path)
        output_file_path: str

        if output_format == "json":
            output_file_path = f"{document_name}.json"
            result.json(output_file_path)

        elif output_format == "markdown":
            output_file_path = f"{document_name}.md"
            result.markdown(output_file_path)

        else:
            return "Invalid output format."

        with open(output_file_path, "r") as f:
            extracted_text = f.read()
        f.close()
        return extracted_text

    @retry(requests.RequestException, delay=30, backoff=2, max_delay=180)
    def _extract_webpage_content(self, url: str) -> str:
        api_key = os.getenv("FIRECRAWL_API_KEY")
        from firecrawl import FirecrawlApp

        # Initialize the FirecrawlApp with your API key
        app = FirecrawlApp(api_key=api_key)

        data = app.crawl_url(url, params={"limit": 1, "scrapeOptions": {"formats": ["markdown"]}})
        logger.debug(f"Extractred data from {url}: {data}")
        if len(data["data"]) == 0:
            if data["success"] == True:
                return "No content found on the webpage."
            else:
                return "Error while crawling the webpage."

        return str(data["data"][0]["markdown"])

    def _download_file(self, url: str):
        r"""Download a file from a URL and save it to the cache directory."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            file_name = url.split("/")[-1]

            file_path = os.path.join(self.cache_dir, file_name)

            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            return file_path

        except requests.exceptions.RequestException as e:
            print(f"Error downloading the file: {e}")

    def _get_formatted_time(self) -> str:
        import time

        return time.strftime("%m%d%H%M")

    def _unzip_file(self, zip_path: str) -> List[str]:
        if not zip_path.endswith(".zip"):
            raise ValueError("Only .zip files are supported")

        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        extract_path = os.path.join(self.cache_dir, zip_name)
        os.makedirs(extract_path, exist_ok=True)

        try:
            subprocess.run(["unzip", "-o", zip_path, "-d", extract_path], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to unzip file: {e}")

        extracted_files = []
        for root, _, files in os.walk(extract_path):
            for file in files:
                extracted_files.append(os.path.join(root, file))

        return extracted_files

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects representing the functions in the toolkit.
        """
        return [
            FunctionTool(self.extract_document_content),
        ]
