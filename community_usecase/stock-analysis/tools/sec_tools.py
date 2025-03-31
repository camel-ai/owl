from typing import List
from typing import Optional
from camel.toolkits.base import BaseToolkit
from camel.toolkits.function_tool import FunctionTool
from camel.utils import api_keys_required, dependencies_required
import requests
import html2text
import re

class SECToolkit(BaseToolkit):
    r"""A class representing a toolkit for SEC filings analysis.
    
    This toolkit provides functionality to:
    - Fetch and process 10-K (annual) reports
    - Fetch and process 10-Q (quarterly) reports
    - Clean and format filing content for analysis
    - Support semantic search capabilities on filing content
    
    The toolkit requires SEC API credentials and handles HTTP requests
    to SEC's EDGAR database to retrieve filing documents.
    """

    @dependencies_required("sec_api")
    @api_keys_required(
        [
            (None, "SEC_API_API_KEY"),
        ]
    )
    def fetch_10k_filing(self, stock_name: str) -> Optional[str]:
        r"""Fetches and processes the latest 10-K form content for a given stock symbol.

        This function retrieves the most recent 10-K filing from SEC's database using
        the provided stock ticker symbol. It downloads the filing content, converts
        it from HTML to text format, and performs text cleaning.

        Args:
            stock_name (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).

        Returns:
            Optional[str]: A cleaned text version of the 10-K filing content.
                Returns None in the following cases:
                - No filings found for the given stock symbol
                - HTTP errors during content retrieval
                - Other exceptions during processing
                
                The returned text is preprocessed to:
                - Remove HTML formatting
                - Remove special characters
                - Retain only alphanumeric characters, dollar signs, spaces and newlines
        """
        
        from sec_api import QueryApi
        import os

        try:
            queryApi = QueryApi(api_key=os.environ['SEC_API_API_KEY'])
            query = {
                "query": {
                    "query_string": {
                        "query": f"ticker:{stock_name} AND formType:\"10-K\""
                    }
                },
                "from": "0",
                "size": "1",
                "sort": [{ "filedAt": { "order": "desc" }}]
            }
            response = queryApi.get_filings(query)
            if response and 'filings' in response:
                filings = response['filings']
            else:
                filings = []
            if len(filings) == 0:
                print("No filings found for this stock.")
                return None

            url = filings[0]['linkToFilingDetails']
            
            headers = {
                "User-Agent": "crewai.com bisan@crewai.com",
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            h = html2text.HTML2Text()
            h.ignore_links = False
            text = h.handle(response.content.decode("utf-8"))

            text = re.sub(r"[^a-zA-Z$0-9\s\n]", "", text)
            return text
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            print(f"Error fetching 10-K URL: {e}")
            return None
    
    @dependencies_required("sec_api")
    @api_keys_required(
        [
            (None, "SEC_API_API_KEY"),
        ]
    )
    def fetch_10q_filing(self, stock_name: str) -> Optional[str]:
        r"""Fetches and processes the latest 10-Q form content for a given stock symbol.

        This function retrieves the most recent 10-Q filing from SEC's database using
        the provided stock ticker symbol. It downloads the filing content, converts
        it from HTML to text format, and performs text cleaning.

        Args:
            stock_name (str): The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).

        Returns:
            Optional[str]: A cleaned text version of the 10-Q filing content.
                Returns None in the following cases:
                - No filings found for the given stock symbol
                - HTTP errors during content retrieval
                - Other exceptions during processing
                
                The returned text is preprocessed to:
                - Remove HTML formatting
                - Remove special characters
                - Retain only alphanumeric characters, dollar signs, spaces and newlines
        """

        from sec_api import QueryApi
        import os

        try:
            queryApi = QueryApi(api_key=os.environ['SEC_API_API_KEY'])
            query = {
                "query": {
                    "query_string": {
                        "query": f"ticker:{stock_name} AND formType:\"10-Q\""
                    }
                },
                "from": "0",
                "size": "1",
                "sort": [{ "filedAt": { "order": "desc" }}]
            }
            response = queryApi.get_filings(query)
            if response and 'filings' in response:
                filings = response['filings']
            else:
                filings = []
            if len(filings) == 0:
                print("No filings found for this stock.")
                return None

            url = filings[0]['linkToFilingDetails']
            
            headers = {
                "User-Agent": "crewai.com bisan@crewai.com",
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            h = html2text.HTML2Text()
            h.ignore_links = False
            text = h.handle(response.content.decode("utf-8"))

            # Removing all non-English words, dollar signs, numbers, and newlines from text
            text = re.sub(r"[^a-zA-Z$0-9\s\n]", "", text)
            return text
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            print(f"Error fetching 10-Q URL: {e}")
            return None

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """

        return [
            FunctionTool(self.fetch_10k_filing),
            FunctionTool(self.fetch_10q_filing)
        ]

if __name__ == "__main__":
    toolkit = SECToolkit()
    data_10k = toolkit.fetch_10k_filing("GOOG")
    data_10q = toolkit.fetch_10q_filing("GOOG")
    # 检查 data_10k 是否为 None，如果不是则计算长度
    print(f"fetch_10k_filing AAPL = {len(data_10k) if data_10k is not None else 0}")
    print(f"fetch_10q_filing AAPL = {len(data_10q) if data_10q is not None else 0}")