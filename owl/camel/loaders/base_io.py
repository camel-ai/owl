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
import re
from abc import ABC, abstractmethod
from copy import deepcopy
from hashlib import md5
from io import BytesIO
from typing import Any, Dict, List, Optional

from camel.utils import dependencies_required


class File(ABC):
    r"""Represents an uploaded file comprised of Documents.

    Args:
        name (str): The name of the file.
        file_id (str): The unique identifier of the file.
        metadata (Dict[str, Any], optional): Additional metadata
            associated with the file. Defaults to None.
        docs (List[Dict[str, Any]], optional): A list of documents
            contained within the file. Defaults to None.
        raw_bytes (bytes, optional): The raw bytes content of the file.
            Defaults to b"".
    """

    def __init__(
        self,
        name: str,
        file_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        docs: Optional[List[Dict[str, Any]]] = None,
        raw_bytes: bytes = b"",
    ):
        self.name = name
        self.file_id = file_id
        self.metadata = metadata or {}
        self.docs = docs or []
        self.raw_bytes = raw_bytes

    @classmethod
    @abstractmethod
    def from_bytes(cls, file: BytesIO, filename: str) -> "File":
        r"""Creates a File object from a BytesIO object.

        Args:
            file (BytesIO): A BytesIO object representing the contents of the
                file.
            filename (str): The name of the file.

        Returns:
            File: A File object.
        """
        pass

    @classmethod
    def from_raw_bytes(cls, raw_bytes: bytes, filename: str) -> "File":
        r"""Creates a File object from raw bytes.

        Args:
            raw_bytes (bytes): The raw bytes content of the file.
            filename (str): The name of the file.

        Returns:
            File: A File object.
        """
        file = BytesIO(raw_bytes)
        return cls.from_bytes(file, filename)

    @staticmethod
    def create_file(file: BytesIO, filename: str) -> "File":
        r"""Reads an uploaded file and returns a File object.

        Args:
            file (BytesIO): A BytesIO object representing the contents of the
                file.
            filename (str): The name of the file.

        Returns:
            File: A File object.
        """
        ext_to_cls = {
            "docx": DocxFile,
            "pdf": PdfFile,
            "txt": TxtFile,
            "json": JsonFile,
            "html": HtmlFile,
        }

        ext = filename.split(".")[-1].lower()
        if ext not in ext_to_cls:
            raise NotImplementedError(f"File type {ext} not supported")

        out_file = ext_to_cls[ext].from_bytes(file, filename)
        return out_file

    @staticmethod
    def create_file_from_raw_bytes(raw_bytes: bytes, filename: str) -> "File":
        r"""Reads raw bytes and returns a File object.

        Args:
            raw_bytes (bytes): The raw bytes content of the file.
            filename (str): The name of the file.

        Returns:
            File: A File object.
        """
        file = BytesIO(raw_bytes)
        return File.create_file(file, filename)

    def __repr__(self) -> str:
        return f"File(name={self.name}, id={self.file_id}, " f"metadata={self.metadata}, docs={self.docs})"

    def __str__(self) -> str:
        return f"File(name={self.name}, id={self.file_id}, metadata=" f"{self.metadata})"

    def copy(self) -> "File":
        r"""Create a deep copy of this File"""

        return self.__class__(
            name=self.name,
            file_id=self.file_id,
            metadata=deepcopy(self.metadata),
            docs=deepcopy(self.docs),
            raw_bytes=self.raw_bytes,
        )


def strip_consecutive_newlines(text: str) -> str:
    r"""Strips consecutive newlines from a string.

    Args:
        text (str): The string to strip.

    Returns:
        str: The string with consecutive newlines stripped.
    """
    return re.sub(r"\s*\n\s*", "\n", text)


class DocxFile(File):
    @classmethod
    @dependencies_required("docx2txt")
    def from_bytes(cls, file: BytesIO, filename: str) -> "DocxFile":
        r"""Creates a DocxFile object from a BytesIO object.

        Args:
            file (BytesIO): A BytesIO object representing the contents of the
                docx file.
            filename (str): The name of the file.

        Returns:
            DocxFile: A DocxFile object.
        """
        import docx2txt

        text = docx2txt.process(file)
        text = strip_consecutive_newlines(text)
        # Create a dictionary with the extracted text
        doc = {"page_content": text.strip()}
        # Calculate a unique identifier for the file
        file_id = md5(file.getvalue()).hexdigest()
        # Reset the file pointer to the beginning
        file.seek(0)
        return cls(
            name=filename,
            file_id=file_id,
            docs=[doc],
            raw_bytes=file.getvalue(),
        )


class PdfFile(File):
    @classmethod
    def from_bytes(cls, file: BytesIO, filename: str) -> "PdfFile":
        r"""Creates a PdfFile object from a BytesIO object.

        Args:
            file (BytesIO): A BytesIO object representing the contents of the
                pdf file.
            filename (str): The name of the file.

        Returns:
            PdfFile: A PdfFile object.
        """
        # Use fitz to extract text from pdf files
        try:
            import fitz
        except ImportError:
            raise ImportError(
                "Please install `PyMuPDF` first. " "You can install it by running " "`pip install PyMuPDF`."
            )
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        docs = []
        for i, page in enumerate(pdf):
            text = page.get_text(sort=True)
            text = strip_consecutive_newlines(text)
            # Create a dictionary with the extracted text
            doc = {"page_content": text.strip(), "page": i + 1}
            docs.append(doc)
        # Calculate a unique identifier for the file
        file_id = md5(file.getvalue()).hexdigest()
        # Reset the file pointer to the beginning
        file.seek(0)
        return cls(
            name=filename,
            file_id=file_id,
            docs=docs,
            raw_bytes=file.getvalue(),
        )


class TxtFile(File):
    @classmethod
    def from_bytes(cls, file: BytesIO, filename: str) -> "TxtFile":
        r"""Creates a TxtFile object from a BytesIO object.

        Args:
            file (BytesIO): A BytesIO object representing the contents of the
                txt file.
            filename (str): The name of the file.

        Returns:
            TxtFile: A TxtFile object.
        """
        # Read the text from the file
        text = file.read().decode("utf-8")
        text = strip_consecutive_newlines(text)
        # Create a dictionary with the extracted text
        doc = {"page_content": text.strip()}
        # Calculate a unique identifier for the file
        file_id = md5(file.getvalue()).hexdigest()
        # Reset the file pointer to the beginning
        file.seek(0)
        return cls(
            name=filename,
            file_id=file_id,
            docs=[doc],
            raw_bytes=file.getvalue(),
        )


class JsonFile(File):
    @classmethod
    def from_bytes(cls, file: BytesIO, filename: str) -> "JsonFile":
        r"""Creates a JsonFile object from a BytesIO object.

        Args:
            file (BytesIO): A BytesIO object representing the contents of the
                json file.
            filename (str): The name of the file.

        Returns:
            JsonFile: A JsonFile object.
        """
        # Parse the JSON data from the file
        data = json.load(file)
        # Create a dictionary with the parsed data
        doc = {"page_content": json.dumps(data)}
        # Calculate a unique identifier for the file
        file_id = md5(file.getvalue()).hexdigest()
        # Reset the file pointer to the beginning
        file.seek(0)
        return cls(
            name=filename,
            file_id=file_id,
            docs=[doc],
            raw_bytes=file.getvalue(),
        )


class HtmlFile(File):
    @classmethod
    def from_bytes(cls, file: BytesIO, filename: str) -> "HtmlFile":
        r"""Creates a HtmlFile object from a BytesIO object.

        Args:
            file (BytesIO): A BytesIO object representing the contents of the
                html file.
            filename (str): The name of the file.

        Returns:
            HtmlFile: A HtmlFile object.
        """
        # Parse the HTML data from the file
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError(
                "Please install `beautifulsoup4` first. "
                "You can install it by running "
                "`pip install beautifulsoup4`."
            )
        soup = BeautifulSoup(file, "html.parser")
        text = soup.get_text()
        text = strip_consecutive_newlines(text)
        # Create a dictionary with the parsed data
        doc = {"page_content": text.strip()}
        # Calculate a unique identifier for the file
        file_id = md5(file.getvalue()).hexdigest()
        # Reset the file pointer to the beginning
        file.seek(0)
        return cls(
            name=filename,
            file_id=file_id,
            docs=[doc],
            raw_bytes=file.getvalue(),
        )
