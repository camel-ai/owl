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
import time
from typing import Any, Dict, List, Union

from requests.exceptions import RequestException

from camel.toolkits import FunctionTool
from camel.toolkits.base import BaseToolkit


class RedditToolkit(BaseToolkit):
    r"""A class representing a toolkit for Reddit operations.

    This toolkit provides methods to interact with the Reddit API, allowing
    users to collect top posts, perform sentiment analysis on comments, and
    track keyword discussions across multiple subreddits.

    Attributes:
        retries (int): Number of retries for API requests in case of failure.
        delay (int): Delay between retries in seconds.
        reddit (Reddit): An instance of the Reddit client.
    """

    def __init__(self, retries: int = 3, delay: int = 0):
        r"""Initializes the RedditToolkit with the specified number of retries
        and delay.

        Args:
            retries (int): Number of times to retry the request in case of
                failure. Defaults to `3`.
            delay (int): Time in seconds to wait between retries. Defaults to
            `0`.
        """
        from praw import Reddit  # type: ignore[import-untyped]

        self.retries = retries
        self.delay = delay

        self.client_id = os.environ.get("REDDIT_CLIENT_ID", "")
        self.client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
        self.user_agent = os.environ.get("REDDIT_USER_AGENT", "")

        self.reddit = Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
            request_timeout=30,  # Set a timeout to handle delays
        )

    def _retry_request(self, func, *args, **kwargs):
        r"""Retries a function in case of network-related errors.

        Args:
            func (callable): The function to be retried.
            *args: Arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            Any: The result of the function call if successful.

        Raises:
            RequestException: If all retry attempts fail.
        """
        for attempt in range(self.retries):
            try:
                return func(*args, **kwargs)
            except RequestException as e:
                print(f"Attempt {attempt + 1}/{self.retries} failed: {e}")
                if attempt < self.retries - 1:
                    time.sleep(self.delay)
                else:
                    raise

    def collect_top_posts(
        self,
        subreddit_name: str,
        post_limit: int = 5,
        comment_limit: int = 5,
    ) -> Union[List[Dict[str, Any]], str]:
        r"""Collects the top posts and their comments from a specified
        subreddit.

        Args:
            subreddit_name (str): The name of the subreddit to collect posts
                from.
            post_limit (int): The maximum number of top posts to collect.
                Defaults to `5`.
            comment_limit (int): The maximum number of top comments to collect
                per post. Defaults to `5`.

        Returns:
            Union[List[Dict[str, Any]], str]: A list of dictionaries, each
                containing the post title and its top comments if success.
                String warming if credentials are not set.
        """
        if not all([self.client_id, self.client_secret, self.user_agent]):
            return "Reddit API credentials are not set. " "Please set the environment variables."

        subreddit = self._retry_request(self.reddit.subreddit, subreddit_name)
        top_posts = self._retry_request(subreddit.top, limit=post_limit)
        data = []

        for post in top_posts:
            post_data = {
                "Post Title": post.title,
                "Comments": [
                    {"Comment Body": comment.body, "Upvotes": comment.score}
                    for comment in self._retry_request(lambda post=post: list(post.comments))[:comment_limit]
                ],
            }
            data.append(post_data)
            time.sleep(self.delay)  # Add a delay to avoid hitting rate limits

        return data

    def perform_sentiment_analysis(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        r"""Performs sentiment analysis on the comments collected from Reddit
        posts.

        Args:
            data (List[Dict[str, Any]]): A list of dictionaries containing
                Reddit post data and comments.

        Returns:
            List[Dict[str, Any]]: The original data with an added 'Sentiment
                Score' for each comment.
        """
        from textblob import TextBlob

        for item in data:
            # Sentiment analysis should be done on 'Comment Body'
            item["Sentiment Score"] = TextBlob(item["Comment Body"]).sentiment.polarity

        return data

    def track_keyword_discussions(
        self,
        subreddits: List[str],
        keywords: List[str],
        post_limit: int = 10,
        comment_limit: int = 10,
        sentiment_analysis: bool = False,
    ) -> Union[List[Dict[str, Any]], str]:
        r"""Tracks discussions about specific keywords in specified subreddits.

        Args:
            subreddits (List[str]): A list of subreddit names to search within.
            keywords (List[str]): A list of keywords to track in the subreddit
                discussions.
            post_limit (int): The maximum number of top posts to collect per
                subreddit. Defaults to `10`.
            comment_limit (int): The maximum number of top comments to collect
                per post. Defaults to `10`.
            sentiment_analysis (bool): If True, performs sentiment analysis on
                the comments. Defaults to `False`.

        Returns:
            Union[List[Dict[str, Any]], str]: A list of dictionaries
                containing the subreddit name, post title, comment body, and
                upvotes for each comment that contains the specified keywords
                if success. String warming if credentials are not set.
        """
        if not all([self.client_id, self.client_secret, self.user_agent]):
            return "Reddit API credentials are not set. " "Please set the environment variables."

        data = []

        for subreddit_name in subreddits:
            subreddit = self._retry_request(self.reddit.subreddit, subreddit_name)
            top_posts = self._retry_request(subreddit.top, limit=post_limit)

            for post in top_posts:
                for comment in self._retry_request(lambda post=post: list(post.comments))[:comment_limit]:
                    # Print comment body for debugging
                    if any(keyword.lower() in comment.body.lower() for keyword in keywords):
                        comment_data = {
                            "Subreddit": subreddit_name,
                            "Post Title": post.title,
                            "Comment Body": comment.body,
                            "Upvotes": comment.score,
                        }
                        data.append(comment_data)
                # Add a delay to avoid hitting rate limits
                time.sleep(self.delay)
        if sentiment_analysis:
            data = self.perform_sentiment_analysis(data)
        return data

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects for the
                toolkit methods.
        """
        return [
            FunctionTool(self.collect_top_posts),
            FunctionTool(self.perform_sentiment_analysis),
            FunctionTool(self.track_keyword_discussions),
        ]
