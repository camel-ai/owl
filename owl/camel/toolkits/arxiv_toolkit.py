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

from typing import Dict, Generator, List, Optional

from camel.toolkits.base import BaseToolkit
from camel.toolkits.function_tool import FunctionTool
from camel.utils import dependencies_required
from loguru import logger


class ArxivToolkit(BaseToolkit):
    r"""A toolkit for interacting with the arXiv API to search and download
    academic papers.
    """

    @dependencies_required("arxiv")
    def __init__(self) -> None:
        r"""Initializes the ArxivToolkit and sets up the arXiv client."""
        import arxiv

        self.client = arxiv.Client()

    def _get_search_results(
        self,
        query: str,
        paper_ids: Optional[List[str]] = None,
        max_results: Optional[int] = 5,
    ) -> Generator:
        r"""Retrieves search results from the arXiv API based on the provided
        query and optional paper IDs.

        Args:
            query (str): The search query string used to search for papers on
                arXiv.
            paper_ids (List[str], optional): A list of specific arXiv paper
                IDs to search for. (default::obj: `None`)
            max_results (int, optional): The maximum number of search results
                to retrieve. (default::obj: `5`)

        Returns:
            Generator: A generator that yields results from the arXiv search
                query, which includes metadata about each paper matching the
                query.
        """
        import arxiv

        logger.debug(f"Searching for papers with query: {query}")

        paper_ids = paper_ids or []
        search_query = arxiv.Search(
            query=query,
            id_list=paper_ids,
            max_results=max_results,
        )
        return self.client.results(search_query)

    def search_papers(
        self,
        query: str,
        paper_ids: Optional[List[str]] = None,
        max_results: Optional[int] = 5,
    ) -> List[Dict[str, str]]:
        r"""Searches for academic papers on arXiv using a query string and
        optional paper IDs.

        Args:
            query (str): The search query string.
            paper_ids (List[str], optional): A list of specific arXiv paper
                IDs to search for. (default::obj: `None`)
            max_results (int, optional): The maximum number of search results
                to return. (default::obj: `5`)

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each containing
                information about a paper, including title, published date,
                authors, entry ID, summary, and extracted text from the paper.
        """
        from arxiv2text import arxiv_to_text

        search_results = self._get_search_results(query, paper_ids, max_results)
        papers_data = []

        for paper in search_results:
            paper_info = {
                "title": paper.title,
                "published_date": paper.updated.date().isoformat(),
                "authors": [author.name for author in paper.authors],
                "entry_id": paper.entry_id,
                "summary": paper.summary,
                # TODO: Use chunkr instead of atxiv_to_text for better
                # performance
                "paper_text": arxiv_to_text(paper.pdf_url),
            }
            papers_data.append(paper_info)

        return papers_data

    def download_papers(
        self,
        query: str,
        paper_ids: Optional[List[str]] = None,
        max_results: Optional[int] = 5,
        output_dir: Optional[str] = "./",
    ) -> str:
        r"""Downloads PDFs of academic papers from arXiv based on the provided
        query.

        Args:
            query (str): The search query string.
            paper_ids (List[str], optional): A list of specific arXiv paper
                IDs to download. (default::obj: `None`)
            max_results (int, optional): The maximum number of search results
                to download. (default::obj: `5`)
            output_dir (str, optional): The directory to save the downloaded
                PDFs. Defaults to the current directory.

        Returns:
            str: Status message indicating success or failure.
        """
        logger.debug(f"Downloading papers for query: {query}")
        try:
            search_results = self._get_search_results(query, paper_ids, max_results)

            for paper in search_results:
                paper.download_pdf(dirpath=output_dir, filename=f"{paper.title}" + ".pdf")
            return "papers downloaded successfully"
        except Exception as e:
            return f"An error occurred: {e}"

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """
        return [
            FunctionTool(self.search_papers),
            FunctionTool(self.download_papers),
        ]
