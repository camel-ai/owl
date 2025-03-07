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
import re
from typing import Any, Dict, List, Optional

from camel.toolkits import FunctionTool
from camel.toolkits.base import BaseToolkit


class GoogleScholarToolkit(BaseToolkit):
    r"""A toolkit for retrieving information about authors and their
    publications from Google Scholar.

    Attributes:
        author_identifier (Union[str, None]): The author's Google Scholar URL
            or name of the author to search for.
        is_author_name (bool): Flag to indicate if the identifier is a name.
            (default: :obj:`False`)
        scholarly (module): The scholarly module for querying Google Scholar.
        author (Optional[Dict[str, Any]]): Cached author details, allowing
            manual assignment if desired.
    """

    def __init__(self, author_identifier: str, is_author_name: bool = False) -> None:
        r"""Initializes the GoogleScholarToolkit with the author's identifier.

        Args:
            author_identifier (str): The author's Google Scholar URL or name
                of the author to search for.
            is_author_name (bool): Flag to indicate if the identifier is a
                name. (default: :obj:`False`)
        """
        from scholarly import scholarly

        self.scholarly = scholarly
        self.author_identifier = author_identifier
        self.is_author_name = is_author_name
        self._author: Optional[Dict[str, Any]] = None

    @property
    def author(self) -> Dict[str, Any]:
        r"""Getter for the author attribute, fetching details if not cached.

        Returns:
            Dict[str, Any]: A dictionary containing author details. If no data
                is available, returns an empty dictionary.
        """
        if self._author is None:
            self.get_author_detailed_info()
        return self._author or {}

    @author.setter
    def author(self, value: Optional[Dict[str, Any]]) -> None:
        r"""Sets or overrides the cached author information.

        Args:
            value (Optional[Dict[str, Any]]): A dictionary containing author
                details to cache or `None` to clear the cached data.

        Raises:
            ValueError: If `value` is not a dictionary or `None`.
        """
        if value is None or isinstance(value, dict):
            self._author = value
        else:
            raise ValueError("Author must be a dictionary or None.")

    def _extract_author_id(self) -> Optional[str]:
        r"""Extracts the author ID from a Google Scholar URL if provided.

        Returns:
            Optional[str]: The extracted author ID, or None if not found.
        """
        match = re.search(r"user=([A-Za-z0-9-]+)", self.author_identifier)
        return match.group(1) if match else None

    def get_author_detailed_info(
        self,
    ) -> dict:
        r"""Retrieves detailed information about the author.

        Returns:
            dict: A dictionary containing detailed information about the
                author.
        """
        if self.is_author_name:
            search_query = self.scholarly.search_author(self.author_identifier)
            # Retrieve the first result from the iterator
            first_author_result = next(search_query)
        else:
            author_id = self._extract_author_id()
            first_author_result = self.scholarly.search_author_id(id=author_id)

        self._author = self.scholarly.fill(first_author_result)
        return self._author  # type: ignore[return-value]

    def get_author_publications(
        self,
    ) -> List[str]:
        r"""Retrieves the titles of the author's publications.

        Returns:
            List[str]: A list of publication titles authored by the author.
        """
        publication_titles = [pub["bib"]["title"] for pub in self.author["publications"]]
        return publication_titles

    def get_publication_by_title(self, publication_title: str) -> Optional[dict]:
        r"""Retrieves detailed information about a specific publication by its
        title. Note that this method cannot retrieve the full content of the
        paper.

        Args:
            publication_title (str): The title of the publication to search
                for.

        Returns:
            Optional[dict]: A dictionary containing detailed information about
                the publication if found; otherwise, `None`.
        """
        publications = self.author["publications"]
        for publication in publications:
            if publication["bib"]["title"] == publication_title:
                return self.scholarly.fill(publication)
        return None  # Return None if not found

    def get_full_paper_content_by_link(self, pdf_url: str) -> Optional[str]:
        r"""Retrieves the full paper content from a given PDF URL using the
        arxiv2text tool.

        Args:
            pdf_url (str): The URL of the PDF file.

        Returns:
            Optional[str]: The full text extracted from the PDF, or `None` if
                an error occurs.
        """
        from arxiv2text import arxiv_to_text

        try:
            return arxiv_to_text(pdf_url)
        except Exception:
            return None  # Return None in case of any error

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """
        return [
            FunctionTool(self.get_author_detailed_info),
            FunctionTool(self.get_author_publications),
            FunctionTool(self.get_publication_by_title),
            FunctionTool(self.get_full_paper_content_by_link),
        ]
