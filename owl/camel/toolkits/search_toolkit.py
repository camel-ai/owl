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
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, TypeAlias, Union, Tuple

import requests

from camel.toolkits.base import BaseToolkit
from camel.toolkits.function_tool import FunctionTool
from camel.utils import api_keys_required, dependencies_required
from loguru import logger
from retry import retry

from camel.toolkits.base import BaseToolkit
from camel.toolkits import FunctionTool
from camel.messages import BaseMessage
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelType, ModelPlatformType


class SearchToolkit(BaseToolkit):
    r"""A class representing a toolkit for web search.

    This class provides methods for searching information on the web using
    search engines like Google, DuckDuckGo, Wikipedia and Wolfram Alpha, Brave.
    """

    @dependencies_required("wikipedia")
    @retry(ConnectionError, delay=3)
    def search_wiki(self, entity: str) -> str:
        r"""Search the entity in WikiPedia and return the summary of the
            required page, containing factual information about
            the given entity.

        Args:
            entity (str): The entity to be searched.

        Returns:
            str: The search result. If the page corresponding to the entity
                exists, return the summary of this entity in a string.
        """
        import wikipedia

        logger.debug(f"Calling search_wiki function with entity: {entity}")

        result: str

        try:
            page = wikipedia.page(entity)
            result_dict = {
                "url": page.url,
                "title": page.title,
                "content": page.content,
            }
            result = str(result_dict)

        except wikipedia.exceptions.DisambiguationError as e:
            result = wikipedia.summary(e.options[0], sentences=5, auto_suggest=False)
        except wikipedia.exceptions.PageError:
            result = (
                "There is no page in Wikipedia corresponding to entity "
                f"{entity}, please specify another word to describe the"
                " entity to be searched."
            )
        except wikipedia.exceptions.WikipediaException as e:
            result = f"An exception occurred during the search: {e}"

        except Exception as e:
            logger.error(f"An exception occurred during the search: {e}")
            return e
        logger.debug(f"wiki result: {result}")
        return result

    @dependencies_required("duckduckgo_search")
    @retry(delay=5)
    def search_duckduckgo(self, query: str, source: str = "text", max_results: int = 5) -> List[Dict[str, Any]]:
        r"""Use DuckDuckGo search engine to search information for
        the given query.

        This function queries the DuckDuckGo API for related topics to
        the given search term. The results are formatted into a list of
        dictionaries, each representing a search result.

        Args:
            query (str): The query to be searched.
            source (str): The type of information to query (e.g., "text",
                "images", "videos"). Defaults to "text".
            max_results (int): Max number of results, defaults to `5`.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary
                represents a search result.
        """
        from duckduckgo_search import DDGS
        from requests.exceptions import RequestException

        logger.debug(f"Calling search_duckduckgo function with query: {query}")

        ddgs = DDGS()
        responses: List[Dict[str, Any]] = []

        if source == "text":
            try:
                results = ddgs.text(keywords=query, max_results=max_results)
            except RequestException as e:
                # Handle specific exceptions or general request exceptions
                responses.append({"error": f"duckduckgo search failed.{e}"})

            # Iterate over results found
            for i, result in enumerate(results, start=1):
                # Creating a response object with a similar structure
                response = {
                    "result_id": i,
                    "title": result["title"],
                    "description": result["body"],
                    "url": result["href"],
                }
                responses.append(response)

        elif source == "images":
            try:
                results = ddgs.images(keywords=query, max_results=max_results)
            except RequestException as e:
                # Handle specific exceptions or general request exceptions
                responses.append({"error": f"duckduckgo search failed.{e}"})

            # Iterate over results found
            for i, result in enumerate(results, start=1):
                # Creating a response object with a similar structure
                response = {
                    "result_id": i,
                    "title": result["title"],
                    "image": result["image"],
                    "url": result["url"],
                    "source": result["source"],
                }
                responses.append(response)

        elif source == "videos":
            try:
                results = ddgs.videos(keywords=query, max_results=max_results)
            except RequestException as e:
                # Handle specific exceptions or general request exceptions
                responses.append({"error": f"duckduckgo search failed.{e}"})

            # Iterate over results found
            for i, result in enumerate(results, start=1):
                # Creating a response object with a similar structure
                response = {
                    "result_id": i,
                    "title": result["title"],
                    "description": result["description"],
                    "embed_url": result["embed_url"],
                    "publisher": result["publisher"],
                    "duration": result["duration"],
                    "published": result["published"],
                }
                responses.append(response)
        # If no answer found, return an empty list
        additional_text = """
            Here are some tips to help you get the most out of your search results:
            - When dealing with web snippets, keep in mind that they are often brief and lack specific details. If the snippet doesn't provide useful information, but the URL is from a highly-ranked source, it might still contain the data you need. 
            - For more detailed answers, you should utilize other tools to analyze the content of the websites in the search results, e.g. document relevant toolkit.
            - When seeking specific quantities, it's essential to look for a reliable and accurate source. Avoid relying solely on web snippets for figures like dollar amounts, as they may be imprecise or approximated.
            - If the information found in the snippets doesn't answer your original query satisfactorily, make sure to check the first URL. This is likely to contain much more in-depth content, as it's ranked as the most relevant. 
            - Additionally, when looking for books, consider searching for publicly available full-text PDFs, which can be searched entirely at once using document tools for relevant content.
        """
        logger.debug(f"Search results: {responses}")
        return responses

    @api_keys_required("BRAVE_API_KEY")
    def search_brave(
        self,
        q: str,
        country: str = "US",
        search_lang: str = "en",
        ui_lang: str = "en-US",
        count: int = 20,
        offset: int = 0,
        safesearch: str = "moderate",
        freshness: Optional[str] = None,
        text_decorations: bool = True,
        spellcheck: bool = True,
        result_filter: Optional[str] = None,
        goggles_id: Optional[str] = None,
        units: Optional[str] = None,
        extra_snippets: Optional[bool] = None,
        summary: Optional[bool] = None,
    ) -> Dict[str, Any]:
        r"""This function queries the Brave search engine API and returns a
        dictionary, representing a search result.
        See https://api.search.brave.com/app/documentation/web-search/query
        for more details.

        Args:
            q (str): The user's search query term. Query cannot be empty.
                Maximum of 400 characters and 50 words in the query.
            country (str): The search query country where results come from.
                The country string is limited to 2 character country codes of
                supported countries. For a list of supported values, see
                Country Codes. (default::obj:`US `)
            search_lang (str): The search language preference. The 2 or more
                character language code for which search results are provided.
                For a list of possible values, see Language Codes.
            ui_lang (str): User interface language preferred in response.
                Usually of the format '<language_code>-<country_code>'. For
                more, see RFC 9110. For a list of supported values, see UI
                Language Codes.
            count (int): The number of search results returned in response.
                The maximum is 20. The actual number delivered may be less than
                requested. Combine this parameter with offset to paginate
                search results.
            offset (int): The zero based offset that indicates number of search
                results per page (count) to skip before returning the result.
                The maximum is 9. The actual number delivered may be less than
                requested based on the query. In order to paginate results use
                this parameter together with count. For example, if your user
                interface displays 20 search results per page, set count to 20
                and offset to 0 to show the first page of results. To get
                subsequent pages, increment offset by 1 (e.g. 0, 1, 2). The
                results may overlap across multiple pages.
            safesearch (str): Filters search results for adult content.
                The following values are supported:
                - 'off': No filtering is done.
                - 'moderate': Filters explicit content, like images and videos,
                    but allows adult domains in the search results.
                - 'strict': Drops all adult content from search results.
            freshness (Optional[str]): Filters search results by when they were
                discovered:
                - 'pd': Discovered within the last 24 hours.
                - 'pw': Discovered within the last 7 Days.
                - 'pm': Discovered within the last 31 Days.
                - 'py': Discovered within the last 365 Days.
                - 'YYYY-MM-DDtoYYYY-MM-DD': Timeframe is also supported by
                    specifying the date range e.g. '2022-04-01to2022-07-30'.
            text_decorations (bool): Whether display strings (e.g. result
                snippets) should include decoration markers (e.g. highlighting
                characters).
            spellcheck (bool): Whether to spellcheck provided query. If the
                spellchecker is enabled, the modified query is always used for
                search. The modified query can be found in altered key from the
                query response model.
            result_filter (Optional[str]): A comma delimited string of result
                types to include in the search response. Not specifying this
                parameter will return back all result types in search response
                where data is available and a plan with the corresponding
                option is subscribed. The response always includes query and
                type to identify any query modifications and response type
                respectively. Available result filter values are:
                - 'discussions'
                - 'faq'
                - 'infobox'
                - 'news'
                - 'query'
                - 'summarizer'
                - 'videos'
                - 'web'
                - 'locations'
            goggles_id (Optional[str]): Goggles act as a custom re-ranking on
                top of Brave's search index. For more details, refer to the
                Goggles repository.
            units (Optional[str]): The measurement units. If not provided,
                units are derived from search country. Possible values are:
                - 'metric': The standardized measurement system
                - 'imperial': The British Imperial system of units.
            extra_snippets (Optional[bool]): A snippet is an excerpt from a
                page you get as a result of the query, and extra_snippets
                allow you to get up to 5 additional, alternative excerpts. Only
                available under Free AI, Base AI, Pro AI, Base Data, Pro Data
                and Custom plans.
            summary (Optional[bool]): This parameter enables summary key
                generation in web search results. This is required for
                summarizer to be enabled.

        Returns:
            Dict[str, Any]: A dictionary representing a search result.
        """

        import requests

        BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Content-Type": "application/json",
            "X-BCP-APIV": "1.0",
            "X-Subscription-Token": BRAVE_API_KEY,
        }

        ParamsType: TypeAlias = Dict[
            str,
            Union[str, int, float, List[Union[str, int, float]], None],
        ]

        params: ParamsType = {
            "q": q,
            "country": country,
            "search_lang": search_lang,
            "ui_lang": ui_lang,
            "count": count,
            "offset": offset,
            "safesearch": safesearch,
            "freshness": freshness,
            "text_decorations": text_decorations,
            "spellcheck": spellcheck,
            "result_filter": result_filter,
            "goggles_id": goggles_id,
            "units": units,
            "extra_snippets": extra_snippets,
            "summary": summary,
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()["web"]
        return data

    @api_keys_required("GOOGLE_API_KEY", "SEARCH_ENGINE_ID")
    def search_google(self, query: str, num_result_pages: int = 6) -> List[Dict[str, Any]]:
        r"""Use Google search engine to search information for the given query.

        Args:
            query (str): The query to be searched. The fewer keywords the better。
            num_result_pages (int): The number of result pages to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary
            represents a website.
                Each dictionary contains the following keys:
                - 'result_id': A number in order.
                - 'title': The title of the website.
                - 'description': A brief description of the website.
                - 'long_description': More detail of the website.
                - 'url': The URL of the website.

                Example:
                {
                    'result_id': 1,
                    'title': 'OpenAI',
                    'description': 'An organization focused on ensuring that
                    artificial general intelligence benefits all of humanity.',
                    'long_description': 'OpenAI is a non-profit artificial
                    intelligence research company. Our goal is to advance
                    digital intelligence in the way that is most likely to
                    benefit humanity as a whole',
                    'url': 'https://www.openai.com'
                }
            title, description, url of a website.
        """
        import requests

        logger.debug(f"Calling search_google function with query: {query}")

        # https://developers.google.com/custom-search/v1/overview
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        # https://cse.google.com/cse/all
        SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

        # Using the first page
        start_page_idx = 1
        # Different language may get different result
        search_language = "en"
        # How many pages to return
        num_result_pages = num_result_pages
        # Constructing the URL
        # Doc: https://developers.google.com/custom-search/v1/using_rest
        url = (
            f"https://www.googleapis.com/customsearch/v1?"
            f"key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}&start="
            f"{start_page_idx}&lr={search_language}&num={num_result_pages}"
        )
        if_success = False
        responses = []
        # Fetch the results given the URL
        try:
            # breakpoint()
            # Make the get
            result = requests.get(url)
            result.raise_for_status()
            data = result.json()

            # Get the result items
            if "items" in data:
                search_items = data.get("items")

                # Iterate over 10 results found
                for i, search_item in enumerate(search_items, start=1):
                    # Check metatags are present
                    if "pagemap" not in search_item:
                        continue
                    if "metatags" not in search_item["pagemap"]:
                        continue
                    if "og:description" in search_item["pagemap"]["metatags"][0]:
                        long_description = search_item["pagemap"]["metatags"][0]["og:description"]
                    else:
                        long_description = "N/A"
                    # Get the page title
                    title = search_item.get("title")
                    # Page snippet
                    snippet = search_item.get("snippet")

                    # Extract the page url
                    link = search_item.get("link")
                    response = {
                        "result_id": i,
                        "title": title,
                        "description": snippet,
                        "long_description": long_description,
                        "url": link,
                    }
                    if "huggingface.co" in link:
                        logger.warning(f"Filter out the link: {link}")
                        continue
                    responses.append(response)
                    if_success = True
            else:
                responses.append({"error": f"google search failed with response: {data}"})

        # except requests.RequestException:
        #     # Handle specific exceptions or general request exceptions
        #     responses.append({"error": "google search failed."})
        except Exception as e:
            logger.error(f"Google search failed with error: {e}")
            responses.append({"error": f"google search failed with error: {e}"})

        # If no answer found, return an empty list

        # breakpoint()
        if len(responses) == 0:
            responses.append(
                "No relevant webpages found. Please simplify your query and expand the search space as much as you can, then try again."
            )
        logger.debug(f"search result: {responses}")
        responses.append(
            "If the search result does not contain the information you want, please make reflection on your query: what went well, what didn't, then refine your search plan."
        )
        return responses

    @dependencies_required("wolframalpha")
    def query_wolfram_alpha(self, query: str, is_detailed: bool = False) -> Union[str, Dict[str, Any]]:
        r"""Queries Wolfram|Alpha and returns the result. Wolfram|Alpha is an
        answer engine developed by Wolfram Research. It is offered as an online
        service that answers factual queries by computing answers from
        externally sourced data.

        Args:
            query (str): The query to send to Wolfram Alpha.
            is_detailed (bool): Whether to include additional details
                including step by step information in the result.
                (default::obj:`False`)

        Returns:
            Union[str, Dict[str, Any]]: The result from Wolfram Alpha.
                Returns a string if `is_detailed` is False, otherwise returns
                a dictionary with detailed information.
        """
        import wolframalpha

        WOLFRAMALPHA_APP_ID = os.environ.get("WOLFRAMALPHA_APP_ID")
        if not WOLFRAMALPHA_APP_ID:
            raise ValueError(
                "`WOLFRAMALPHA_APP_ID` not found in environment "
                "variables. Get `WOLFRAMALPHA_APP_ID` here: "
                "`https://products.wolframalpha.com/api/`."
            )

        try:
            client = wolframalpha.Client(WOLFRAMALPHA_APP_ID)
            res = client.query(query)

        except Exception as e:
            return f"Wolfram Alpha wasn't able to answer it. Error: {e}"

        pased_result = self._parse_wolfram_result(res)

        if is_detailed:
            step_info = self._get_wolframalpha_step_by_step_solution(WOLFRAMALPHA_APP_ID, query)
            pased_result["steps"] = step_info
            return pased_result

        return pased_result["final_answer"]

    def _parse_wolfram_result(self, result) -> Dict[str, Any]:
        r"""Parses a Wolfram Alpha API result into a structured dictionary
        format.

        Args:
            result: The API result returned from a Wolfram Alpha
                query, structured with multiple pods, each containing specific
                information related to the query.

        Returns:
            dict: A structured dictionary with the original query and the
                final answer.
        """

        # Extract the original query
        query = result.get("@inputstring", "")

        # Initialize a dictionary to hold structured output
        output = {"query": query, "pod_info": [], "final_answer": None}

        # Loop through each pod to extract the details
        for pod in result.get("pod", []):
            # Handle the case where subpod might be a list
            subpod_data = pod.get("subpod", {})
            if isinstance(subpod_data, list):
                # If it's a list, get the first item for 'plaintext' and 'img'
                description, image_url = next(
                    (
                        (data["plaintext"], data["img"])
                        for data in subpod_data
                        if "plaintext" in data and "img" in data
                    ),
                    ("", ""),
                )
            else:
                # Otherwise, handle it as a dictionary
                description = subpod_data.get("plaintext", "")
                image_url = subpod_data.get("img", {}).get("@src", "")

            pod_info = {
                "title": pod.get("@title", ""),
                "description": description,
                "image_url": image_url,
            }

            # Add to steps list
            output["pod_info"].append(pod_info)

            # Get final answer
            if pod.get("@primary", False):
                output["final_answer"] = description

        return output

    def _get_wolframalpha_step_by_step_solution(self, app_id: str, query: str) -> dict:
        r"""Retrieve a step-by-step solution from the Wolfram Alpha API for a
        given query.

        Args:
            app_id (str): Your Wolfram Alpha API application ID.
            query (str): The mathematical or computational query to solve.

        Returns:
            dict: The step-by-step solution response text from the Wolfram
                Alpha API.
        """
        # Define the base URL
        url = "https://api.wolframalpha.com/v2/query"

        # Set up the query parameters
        params = {
            "appid": app_id,
            "input": query,
            "podstate": ["Result__Step-by-step solution", "Show all steps"],
            "format": "plaintext",
        }

        # Send the request
        response = requests.get(url, params=params)
        root = ET.fromstring(response.text)

        # Extracting step-by-step steps, including 'SBSStep' and 'SBSHintStep'
        steps = []
        # Find all subpods within the 'Results' pod
        for subpod in root.findall(".//pod[@title='Results']//subpod"):
            # Check if the subpod has the desired stepbystepcontenttype
            content_type = subpod.find("stepbystepcontenttype")
            if content_type is not None and content_type.text in [
                "SBSStep",
                "SBSHintStep",
            ]:
                plaintext = subpod.find("plaintext")
                if plaintext is not None and plaintext.text:
                    step_text = plaintext.text.strip()
                    cleaned_step = step_text.replace("Hint: |", "").strip()  # Remove 'Hint: |' if present
                    steps.append(cleaned_step)

        # Structuring the steps into a dictionary
        structured_steps = {}
        for i, step in enumerate(steps, start=1):
            structured_steps[f"step{i}"] = step

        return structured_steps

    def tavily_search(self, query: str, num_results: int = 5, **kwargs) -> List[Dict[str, Any]]:
        r"""Use Tavily Search API to search information for the given query.

        Args:
            query (str): The query to be searched.
            num_results (int): The number of search results to retrieve
                (default is `5`).
            **kwargs: Additional optional parameters supported by Tavily's API:
                - search_depth (str): "basic" or "advanced" search depth.
                - topic (str): The search category, e.g., "general" or "news."
                - days (int): Time frame in days for news-related searches.
                - max_results (int): Max number of results to return
                  (overrides `num_results`).
                See https://docs.tavily.com/docs/python-sdk/tavily-search/
                api-reference for details.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing search
                results. Each dictionary contains:
                - 'result_id' (int): The result's index.
                - 'title' (str): The title of the result.
                - 'description' (str): A brief description of the result.
                - 'long_description' (str): Detailed information, if available.
                - 'url' (str): The URL of the result.
                - 'content' (str): Relevant content from the search result.
                - 'images' (list): A list of related images (if
                  `include_images` is True).
                - 'published_date' (str): Publication date for news topics
                  (if available).
        """
        from tavily import TavilyClient  # type: ignore[import-untyped]

        Tavily_API_KEY = os.getenv("TAVILY_API_KEY")
        if not Tavily_API_KEY:
            raise ValueError(
                "`TAVILY_API_KEY` not found in environment variables. "
                "Get `TAVILY_API_KEY` here: `https://www.tavily.com/api/`."
            )

        client = TavilyClient(Tavily_API_KEY)

        try:
            results = client.search(query, max_results=num_results, **kwargs)
            return results
        except Exception as e:
            return [{"error": f"An unexpected error occurred: {e!s}"}]

    def search_archived_webpage(self, url: str, date: str) -> Tuple[bool, str]:
        r"""Given a url, search the wayback machine and returns the archived version of the url for a given date.

        Args:
            url (str): The url to search for.
            date (str): The date to search for. The format should be YYYYMMDD.
        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating whether the archived version was found and the information to be returned.
        """
        logger.debug(f"Calling search_archived_webpage with url {url} and date {date}")
        try:
            no_timestamp_url = f"https://archive.org/wayback/available?url={url}"
            archive_url = no_timestamp_url + f"&timestamp={date}"
            response = requests.get(archive_url).json()
            response_notimestamp = requests.get(no_timestamp_url).json()
            if "archived_snapshots" in response and "closest" in response["archived_snapshots"]:
                closest = response["archived_snapshots"]["closest"]

            elif (
                "archived_snapshots" in response_notimestamp
                and "closest" in response_notimestamp["archived_snapshots"]
            ):
                closest = response_notimestamp["archived_snapshots"]["closest"]
            else:
                return False, f"The url {url} was not archived on Wayback Machine, please try a different url."

            target_url = closest["url"]
            return True, f"The archived version of the url {url} is {target_url}"
        except Exception as e:
            logger.warning(f"Error in search_archived_webpage: {e}")
            return False, f"An unexpected error occurred: {e!s}"

    def web_search(self, question: str) -> str:
        r"""Performs web search about the given query, and return the search result, contaning relevant urls and results.
        If searching result does not include relevant information, you need to try other ways to solve the task instead of calling this tool again and again.

        Args:
            question (str): The questions which wanting to obtain relevant information through online searches.

        Returns:
            The search result containing url and necessary information.
        """

        model = ModelFactory.create(
            model_type=ModelType.GPT_4O_MINI,
            model_platform=ModelPlatformType.OPENAI,
            model_config_dict={"temperature": 0, "top_p": 1},
        )

        search_agent = ChatAgent(
            "You are a helpful search agent.",
            model=model,
            tools=[
                FunctionTool(self.search_wiki),
                FunctionTool(self.search_google),
                FunctionTool(self.search_archived_webpage),
            ],
        )

        prompt = f"""
Please act as a search agent, constructing appropriate keywords and searach terms, using search toolkit to collect relevant information, including urls, webpage snapshots, etc.
Here are some tips that help you perform web search:
- Never add too many keywords in your search query! Some detailed results need to perform browser interaction to get, not using search toolkit.
- If the question is complex, search results typically do not provide precise answers. It is not likely to find the answer directly using search toolkit only, the search query should be concise and focuses on finding official sources rather than direct answers.
  For example, as for the question "What is the maximum length in meters of #9 in the first National Geographic short on YouTube that was ever released according to the Monterey Bay Aquarium website?", your first search term must be coarse-grained like "National Geographic YouTube" to find the youtube website first, and then try other fine-grained search terms step-by-step to find more urls.
- The results you return do not have to directly answer the original question, you only need to collect relevant information.

Here are the question: {question}

Please perform web search and return the listed search result, including urls and necessary webpage snapshots, introductions, etc.
Your output should be like the followings (at most 3 relevant pages from coa):
[
    {{
        "url": [URL],
        "information": [INFORMATION OR CONTENT]
    }},
    ...
]
"""

        resp = search_agent.step(prompt)
        search_result = resp.msgs[0].content
        logger.debug(f"Response from search agent: {search_result}")

        return search_result

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """
        return [
            # FunctionTool(self.search_wiki),
            # FunctionTool(self.search_google),
            # FunctionTool(self.search_duckduckgo),
            # FunctionTool(self.query_wolfram_alpha),
            # FunctionTool(self.tavily_search),
            # FunctionTool(self.search_brave),
            FunctionTool(self.web_search)
        ]
