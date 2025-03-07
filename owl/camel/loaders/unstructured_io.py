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
import uuid
import warnings
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)

if TYPE_CHECKING:
    from unstructured.documents.elements import Element
import pdb


class UnstructuredIO:
    r"""A class to handle various functionalities provided by the
    Unstructured library, including version checking, parsing, cleaning,
    extracting, staging, chunking data, and integrating with cloud
    services like S3 and Azure for data connection.

    References:
        https://docs.unstructured.io/
    """

    @staticmethod
    def create_element_from_text(
        text: str,
        element_id: Optional[str] = None,
        embeddings: Optional[List[float]] = None,
        filename: Optional[str] = None,
        file_directory: Optional[str] = None,
        last_modified: Optional[str] = None,
        filetype: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> "Element":
        r"""Creates a Text element from a given text input, with optional
        metadata and embeddings.

        Args:
            text (str): The text content for the element.
            element_id (Optional[str], optional): Unique identifier for the
                element. (default: :obj:`None`)
            embeddings (List[float], optional): A list of float
                numbers representing the text embeddings.
                (default: :obj:`None`)
            filename (Optional[str], optional): The name of the file the
                element is associated with. (default: :obj:`None`)
            file_directory (Optional[str], optional): The directory path where
                the file is located. (default: :obj:`None`)
            last_modified (Optional[str], optional): The last modified date of
                the file. (default: :obj:`None`)
            filetype (Optional[str], optional): The type of the file.
                (default: :obj:`None`)
            parent_id (Optional[str], optional): The identifier of the parent
                element. (default: :obj:`None`)

        Returns:
            Element: An instance of Text with the provided content and
                metadata.
        """
        from unstructured.documents.elements import ElementMetadata, Text

        metadata = ElementMetadata(
            filename=filename,
            file_directory=file_directory,
            last_modified=last_modified,
            filetype=filetype,
            parent_id=parent_id,
        )

        return Text(
            text=text,
            element_id=element_id or str(uuid.uuid4()),
            metadata=metadata,
            embeddings=embeddings,
        )

    @staticmethod
    def parse_file_or_url(
        input_path: str,
        **kwargs: Any,
    ) -> Union[List["Element"], None]:
        r"""Loads a file or a URL and parses its contents into elements.

        Args:
            input_path (str): Path to the file or URL to be parsed.
            **kwargs: Extra kwargs passed to the partition function.

        Returns:
            Union[List[Element],None]: List of elements after parsing the file
                or URL if success.

        Raises:
            FileNotFoundError: If the file does not exist at the path
                specified.

        Notes:
            Supported file types:
                "csv", "doc", "docx", "epub", "image", "md", "msg", "odt",
                "org", "pdf", "ppt", "pptx", "rtf", "rst", "tsv", "xlsx".

        References:
            https://unstructured-io.github.io/unstructured/
        """
        import os
        from urllib.parse import urlparse

        from unstructured.partition.auto import partition

        # Check if the input is a URL
        parsed_url = urlparse(input_path)
        # pdb.set_trace()
        is_url = all([parsed_url.scheme, parsed_url.netloc])

        # Handling URL
        if is_url:
            try:
                elements = partition(url=input_path, **kwargs)
                return elements
            except Exception:
                warnings.warn(f"Failed to parse the URL: {input_path}")
                return None

        # Handling file
        else:
            # Check if the file exists
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"The file {input_path} was not found.")

            # Read the file
            try:
                with open(input_path, "rb") as f:
                    elements = partition(file=f, **kwargs)
                    return elements
            except Exception:
                warnings.warn(f"Failed to partition the file: {input_path}")
                return None

    @staticmethod
    def parse_bytes(file: IO[bytes], **kwargs: Any) -> Union[List["Element"], None]:
        r"""Parses a bytes stream and converts its contents into elements.

        Args:
            file (IO[bytes]): The file in bytes format to be parsed.
            **kwargs: Extra kwargs passed to the partition function.

        Returns:
            Union[List[Element], None]: List of elements after parsing the file
                if successful, otherwise `None`.

        Notes:
            Supported file types:
                "csv", "doc", "docx", "epub", "image", "md", "msg", "odt",
                "org", "pdf", "ppt", "pptx", "rtf", "rst", "tsv", "xlsx".

        References:
            https://docs.unstructured.io/open-source/core-functionality/partitioning
        """

        from unstructured.partition.auto import partition

        try:
            # Use partition to process the bytes stream
            elements = partition(file=file, **kwargs)
            return elements
        except Exception as e:
            warnings.warn(f"Failed to partition the file stream: {e}")
            return None

    @staticmethod
    def clean_text_data(
        text: str,
        clean_options: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
    ) -> str:
        r"""Cleans text data using a variety of cleaning functions provided by
        the `unstructured` library.

        This function applies multiple text cleaning utilities by calling the
        `unstructured` library's cleaning bricks for operations like
        replacing Unicode quotes, removing extra whitespace, dashes, non-ascii
        characters, and more.

        If no cleaning options are provided, a default set of cleaning
        operations is applied. These defaults including operations
        "replace_unicode_quotes", "clean_non_ascii_chars",
        "group_broken_paragraphs", and "clean_extra_whitespace".

        Args:
            text (str): The text to be cleaned.
            clean_options (dict): A dictionary specifying which cleaning
                options to apply. The keys should match the names of the
                cleaning functions, and the values should be dictionaries
                containing the parameters for each function. Supported types:
                'clean_extra_whitespace', 'clean_bullets',
                'clean_ordered_bullets', 'clean_postfix', 'clean_prefix',
                'clean_dashes', 'clean_trailing_punctuation',
                'clean_non_ascii_chars', 'group_broken_paragraphs',
                'remove_punctuation', 'replace_unicode_quotes',
                'bytes_string_to_string', 'translate_text'.

        Returns:
            str: The cleaned text.

        Raises:
            AttributeError: If a cleaning option does not correspond to a
                valid cleaning function in `unstructured`.

        Notes:
            The 'options' dictionary keys must correspond to valid cleaning
            brick names from the `unstructured` library.
            Each brick's parameters must be provided in a nested dictionary
            as the value for the key.

        References:
            https://unstructured-io.github.io/unstructured/
        """

        from unstructured.cleaners.core import (
            bytes_string_to_string,
            clean_bullets,
            clean_dashes,
            clean_extra_whitespace,
            clean_non_ascii_chars,
            clean_ordered_bullets,
            clean_postfix,
            clean_prefix,
            clean_trailing_punctuation,
            group_broken_paragraphs,
            remove_punctuation,
            replace_unicode_quotes,
        )
        from unstructured.cleaners.translate import translate_text

        cleaning_functions: Any = {
            "clean_extra_whitespace": clean_extra_whitespace,
            "clean_bullets": clean_bullets,
            "clean_ordered_bullets": clean_ordered_bullets,
            "clean_postfix": clean_postfix,
            "clean_prefix": clean_prefix,
            "clean_dashes": clean_dashes,
            "clean_trailing_punctuation": clean_trailing_punctuation,
            "clean_non_ascii_chars": clean_non_ascii_chars,
            "group_broken_paragraphs": group_broken_paragraphs,
            "remove_punctuation": remove_punctuation,
            "replace_unicode_quotes": replace_unicode_quotes,
            "bytes_string_to_string": bytes_string_to_string,
            "translate_text": translate_text,
        }

        # Define default clean options if none are provided
        if clean_options is None:
            clean_options = [
                ("replace_unicode_quotes", {}),
                ("clean_non_ascii_chars", {}),
                ("group_broken_paragraphs", {}),
                ("clean_extra_whitespace", {}),
            ]

        cleaned_text = text
        for func_name, params in clean_options:
            if func_name in cleaning_functions:
                cleaned_text = cleaning_functions[func_name](cleaned_text, **params)
            else:
                raise ValueError(f"'{func_name}' is not a valid function in " "`Unstructured IO`.")

        return cleaned_text

    @staticmethod
    def extract_data_from_text(
        text: str,
        extract_type: Literal[
            "extract_datetimetz",
            "extract_email_address",
            "extract_ip_address",
            "extract_ip_address_name",
            "extract_mapi_id",
            "extract_ordered_bullets",
            "extract_text_after",
            "extract_text_before",
            "extract_us_phone_number",
        ],
        **kwargs,
    ) -> Any:
        r"""Extracts various types of data from text using functions from
        unstructured.cleaners.extract.

        Args:
            text (str): Text to extract data from.
            extract_type (Literal['extract_datetimetz',
                'extract_email_address', 'extract_ip_address',
                'extract_ip_address_name', 'extract_mapi_id',
                'extract_ordered_bullets', 'extract_text_after',
                'extract_text_before', 'extract_us_phone_number']): Type of
                data to extract.
            **kwargs: Additional keyword arguments for specific
                extraction functions.

        Returns:
            Any: The extracted data, type depends on extract_type.

        References:
            https://unstructured-io.github.io/unstructured/
        """

        from unstructured.cleaners.extract import (
            extract_datetimetz,
            extract_email_address,
            extract_ip_address,
            extract_ip_address_name,
            extract_mapi_id,
            extract_ordered_bullets,
            extract_text_after,
            extract_text_before,
            extract_us_phone_number,
        )

        extraction_functions: Any = {
            "extract_datetimetz": extract_datetimetz,
            "extract_email_address": extract_email_address,
            "extract_ip_address": extract_ip_address,
            "extract_ip_address_name": extract_ip_address_name,
            "extract_mapi_id": extract_mapi_id,
            "extract_ordered_bullets": extract_ordered_bullets,
            "extract_text_after": extract_text_after,
            "extract_text_before": extract_text_before,
            "extract_us_phone_number": extract_us_phone_number,
        }

        if extract_type not in extraction_functions:
            raise ValueError(f"Unsupported extract_type: {extract_type}")

        return extraction_functions[extract_type](text, **kwargs)

    @staticmethod
    def stage_elements(
        elements: List[Any],
        stage_type: Literal[
            "convert_to_csv",
            "convert_to_dataframe",
            "convert_to_dict",
            "dict_to_elements",
            "stage_csv_for_prodigy",
            "stage_for_prodigy",
            "stage_for_baseplate",
            "stage_for_datasaur",
            "stage_for_label_box",
            "stage_for_label_studio",
            "stage_for_weaviate",
        ],
        **kwargs,
    ) -> Union[str, List[Dict], Any]:
        r"""Stages elements for various platforms based on the
        specified staging type.

        This function applies multiple staging utilities to format data
        for different NLP annotation and machine learning tools. It uses
        the 'unstructured.staging' module's functions for operations like
        converting to CSV, DataFrame, dictionary, or formatting for
        specific platforms like Prodigy, etc.

        Args:
            elements (List[Any]): List of Element objects to be staged.
            stage_type (Literal['convert_to_csv', 'convert_to_dataframe',
                'convert_to_dict', 'dict_to_elements',
                'stage_csv_for_prodigy', 'stage_for_prodigy',
                'stage_for_baseplate', 'stage_for_datasaur',
                'stage_for_label_box', 'stage_for_label_studio',
                'stage_for_weaviate']): Type of staging to perform.
            **kwargs: Additional keyword arguments specific to
                the staging type.

        Returns:
            Union[str, List[Dict], Any]: Staged data in the
                format appropriate for the specified staging type.

        Raises:
            ValueError: If the staging type is not supported or a required
                argument is missing.
        References:
            https://unstructured-io.github.io/unstructured/
        """

        from unstructured.staging import (
            base,
            baseplate,
            datasaur,
            label_box,
            label_studio,
            prodigy,
            weaviate,
        )

        staging_functions: Any = {
            "convert_to_csv": base.convert_to_csv,
            "convert_to_dataframe": base.convert_to_dataframe,
            "convert_to_dict": base.convert_to_dict,
            "dict_to_elements": base.dict_to_elements,
            "stage_csv_for_prodigy": lambda els, **kw: prodigy.stage_csv_for_prodigy(els, kw.get("metadata", [])),
            "stage_for_prodigy": lambda els, **kw: prodigy.stage_for_prodigy(els, kw.get("metadata", [])),
            "stage_for_baseplate": baseplate.stage_for_baseplate,
            "stage_for_datasaur": lambda els, **kw: datasaur.stage_for_datasaur(els, kw.get("entities", [])),
            "stage_for_label_box": lambda els, **kw: label_box.stage_for_label_box(els, **kw),
            "stage_for_label_studio": lambda els, **kw: label_studio.stage_for_label_studio(els, **kw),
            "stage_for_weaviate": weaviate.stage_for_weaviate,
        }

        if stage_type not in staging_functions:
            raise ValueError(f"Unsupported stage type: {stage_type}")

        return staging_functions[stage_type](elements, **kwargs)

    @staticmethod
    def chunk_elements(elements: List["Element"], chunk_type: str, **kwargs) -> List["Element"]:
        r"""Chunks elements by titles.

        Args:
            elements (List[Element]): List of Element objects to be chunked.
            chunk_type (str): Type chunk going to apply. Supported types:
                'chunk_by_title'.
            **kwargs: Additional keyword arguments for chunking.

        Returns:
            List[Dict]: List of chunked sections.

        References:
            https://unstructured-io.github.io/unstructured/
        """

        from unstructured.chunking.title import chunk_by_title

        chunking_functions = {
            "chunk_by_title": chunk_by_title,
        }

        if chunk_type not in chunking_functions:
            raise ValueError(f"Unsupported chunk type: {chunk_type}")

        # Format chunks into a list of dictionaries (or your preferred format)
        return chunking_functions[chunk_type](elements, **kwargs)
