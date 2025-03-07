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
import datetime
import os
from http import HTTPStatus
from http.client import responses
from typing import Any, Dict, List, Optional, Union

import requests
from requests_oauthlib import OAuth1

from camel.logger import get_logger
from camel.toolkits import FunctionTool
from camel.toolkits.base import BaseToolkit
from camel.utils import api_keys_required

TWEET_TEXT_LIMIT = 280

logger = get_logger(__name__)


@api_keys_required(
    "TWITTER_CONSUMER_KEY",
    "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
)
def create_tweet(
    text: str,
    poll_options: Optional[List[str]] = None,
    poll_duration_minutes: Optional[int] = None,
    quote_tweet_id: Optional[Union[int, str]] = None,
) -> str:
    r"""Creates a new tweet, optionally including a poll or a quote tweet,
    or simply a text-only tweet.

    This function sends a POST request to the Twitter API to create a new
    tweet. The tweet can be a text-only tweet, or optionally include a poll
    or be a quote tweet. A confirmation prompt is presented to the user
    before the tweet is created.

    Args:
        text (str): The text of the tweet. The Twitter character limit for
            a single tweet is 280 characters.
        poll_options (Optional[List[str]]): A list of poll options for a
            tweet with a poll.
        poll_duration_minutes (Optional[int]): Duration of the poll in
            minutes for a tweet with a poll. This is only required
            if the request includes poll_options.
        quote_tweet_id (Optional[Union[int, str]]): Link to the tweet being
            quoted.

    Returns:
        str: A message indicating the success of the tweet creation,
            including the tweet ID and text. If the request to the
            Twitter API is not successful, the return is an error message.

    Note:
        You can only provide either the `quote_tweet_id` parameter or
        the pair of `poll_duration_minutes` and `poll_options` parameters,
        not both.

    Reference:
        https://developer.x.com/en/docs/x-api/tweets/manage-tweets/api-reference/post-tweets
    """
    auth = OAuth1(
        os.getenv("TWITTER_CONSUMER_KEY"),
        os.getenv("TWITTER_CONSUMER_SECRET"),
        os.getenv("TWITTER_ACCESS_TOKEN"),
        os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )
    url = "https://api.x.com/2/tweets"

    # Validate text
    if text is None:
        return "Text cannot be None"

    if len(text) > TWEET_TEXT_LIMIT:
        return f"Text must not exceed {TWEET_TEXT_LIMIT} characters."

    # Validate poll options and duration
    if (poll_options is None) != (poll_duration_minutes is None):
        return "Error: Both `poll_options` and `poll_duration_minutes` must " "be provided together or not at all."

    # Validate exclusive parameters
    if quote_tweet_id is not None and (poll_options or poll_duration_minutes):
        return "Error: Cannot provide both `quote_tweet_id` and " "(`poll_options` or `poll_duration_minutes`)."

    payload: Dict[str, Any] = {"text": text}

    if poll_options is not None and poll_duration_minutes is not None:
        payload["poll"] = {
            "options": poll_options,
            "duration_minutes": poll_duration_minutes,
        }

    if quote_tweet_id is not None:
        payload["quote_tweet_id"] = str(quote_tweet_id)

    # Making the request
    response = requests.post(url, auth=auth, json=payload)

    if response.status_code != HTTPStatus.CREATED:
        error_type = _handle_http_error(response)
        return f"Request returned a(n) {error_type}: " f"{response.status_code} {response.text}"

    json_response = response.json()
    tweet_id = json_response["data"]["id"]
    tweet_text = json_response["data"]["text"]

    return f"Create tweet {tweet_id} successful with content {tweet_text}."


@api_keys_required(
    "TWITTER_CONSUMER_KEY",
    "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
)
def delete_tweet(tweet_id: str) -> str:
    r"""Deletes a tweet with the specified ID for an authorized user.

    This function sends a DELETE request to the Twitter API to delete
    a tweet with the specified ID. Before sending the request, it
    prompts the user to confirm the deletion.

    Args:
        tweet_id (str): The ID of the tweet to delete.

    Returns:
        str: A message indicating the result of the deletion. If the
            deletion was successful, the message includes the ID of the
            deleted tweet. If the deletion was not successful, the message
            includes an error message.

    Reference:
        https://developer.x.com/en/docs/x-api/tweets/manage-tweets/api-reference/delete-tweets-id
    """
    auth = OAuth1(
        os.getenv("TWITTER_CONSUMER_KEY"),
        os.getenv("TWITTER_CONSUMER_SECRET"),
        os.getenv("TWITTER_ACCESS_TOKEN"),
        os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )
    url = f"https://api.x.com/2/tweets/{tweet_id}"
    response = requests.delete(url, auth=auth)

    if response.status_code != HTTPStatus.OK:
        error_type = _handle_http_error(response)
        return f"Request returned a(n) {error_type}: " f"{response.status_code} {response.text}"

    json_response = response.json()

    # `deleted_status` may be True or False.
    # Defaults to False if not found.
    deleted_status = json_response.get("data", {}).get("deleted", False)
    if not deleted_status:
        return f"The tweet with ID {tweet_id} was not deleted. " "Please check the tweet ID and try again."

    return f"Delete tweet {tweet_id} successful."


@api_keys_required(
    "TWITTER_CONSUMER_KEY",
    "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
)
def get_my_user_profile() -> str:
    r"""Retrieves the authenticated user's Twitter profile info.

    This function sends a GET request to the Twitter API to retrieve the
    authenticated user's profile information, including their pinned tweet.
    It then formats this information into a readable report.

    Returns:
        str: A formatted report of the authenticated user's Twitter profile
            information. This includes their ID, name, username,
            description, location, most recent tweet ID, profile image URL,
            account creation date, protection status, verification type,
            public metrics, and pinned tweet information. If the request to
            the Twitter API is not successful, the return is an error message.

    Reference:
        https://developer.x.com/en/docs/x-api/users/lookup/api-reference/get-users-me
    """
    return _get_user_info()


@api_keys_required(
    "TWITTER_CONSUMER_KEY",
    "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
)
def get_user_by_username(username: str) -> str:
    r"""Retrieves one user's Twitter profile info by username (handle).

    This function sends a GET request to the Twitter API to retrieve the
    user's profile information, including their pinned tweet.
    It then formats this information into a readable report.

    Args:
        username (str): The username (handle) of the user to retrieve.

    Returns:
        str: A formatted report of the user's Twitter profile information.
            This includes their ID, name, username, description, location,
            most recent tweet ID, profile image URL, account creation date,
            protection status, verification type, public metrics, and
            pinned tweet information. If the request to the Twitter API is
            not successful, the return is an error message.

    Reference:
        https://developer.x.com/en/docs/x-api/users/lookup/api-reference/get-users-by-username-username
    """
    return _get_user_info(username)


def _get_user_info(username: Optional[str] = None) -> str:
    r"""Generates a formatted report of the user information from the
    JSON response.

    Args:
        username (Optional[str], optional): The username of the user to
            retrieve. If None, the function retrieves the authenticated
            user's profile information. (default: :obj:`None`)

    Returns:
        str: A formatted report of the user's Twitter profile information.
    """
    oauth = OAuth1(
        os.getenv("TWITTER_CONSUMER_KEY"),
        os.getenv("TWITTER_CONSUMER_SECRET"),
        os.getenv("TWITTER_ACCESS_TOKEN"),
        os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )
    url = f"https://api.x.com/2/users/by/username/{username}" if username else "https://api.x.com/2/users/me"

    tweet_fields = ["created_at", "text"]
    user_fields = [
        "created_at",
        "description",
        "id",
        "location",
        "most_recent_tweet_id",
        "name",
        "pinned_tweet_id",
        "profile_image_url",
        "protected",
        "public_metrics",
        "url",
        "username",
        "verified_type",
    ]
    params = {
        "expansions": "pinned_tweet_id",
        "tweet.fields": ",".join(tweet_fields),
        "user.fields": ",".join(user_fields),
    }

    response = requests.get(url, auth=oauth, params=params)

    if response.status_code != HTTPStatus.OK:
        error_type = _handle_http_error(response)
        return f"Request returned a(n) {error_type}: " f"{response.status_code} {response.text}"

    json_response = response.json()

    user_info = json_response.get("data", {})
    pinned_tweet = json_response.get("includes", {}).get("tweets", [{}])[0]

    user_report_entries = [
        f"ID: {user_info['id']}",
        f"Name: {user_info['name']}",
        f"Username: {user_info['username']}",
    ]

    # Define the part of keys that need to be repeatedly processed
    user_info_keys = [
        "description",
        "location",
        "most_recent_tweet_id",
        "profile_image_url",
    ]
    for key in user_info_keys:
        if not (value := user_info.get(key)):
            continue
        new_key = key.replace("_", " ").capitalize()
        user_report_entries.append(f"{new_key}: {value}")

    if "created_at" in user_info:
        created_at = datetime.datetime.strptime(user_info["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        date_str = created_at.strftime("%B %d, %Y at %H:%M:%S")
        user_report_entries.append(f"Account created at: {date_str}")

    protection_status = "private" if user_info["protected"] else "public"
    user_report_entries.append(f"Protected: This user's Tweets are {protection_status}")

    verification_messages = {
        "blue": (
            "The user has a blue verification, typically reserved for "
            "public figures, celebrities, or global brands"
        ),
        "business": (
            "The user has a business verification, typically " "reserved for businesses and corporations"
        ),
        "government": (
            "The user has a government verification, typically " "reserved for government officials or entities"
        ),
        "none": "The user is not verified",
    }
    verification_type = user_info.get("verified_type", "none")
    user_report_entries.append(f"Verified type: {verification_messages.get(verification_type)}")

    if "public_metrics" in user_info:
        metrics = user_info["public_metrics"]
        user_report_entries.append(
            f"Public metrics: "
            f"The user has {metrics.get('followers_count', 0)} followers, "
            f"is following {metrics.get('following_count', 0)} users, "
            f"has made {metrics.get('tweet_count', 0)} tweets, "
            f"is listed in {metrics.get('listed_count', 0)} lists, "
            f"and has received {metrics.get('like_count', 0)} likes"
        )

    if "pinned_tweet_id" in user_info:
        user_report_entries.append(f"Pinned tweet ID: {user_info['pinned_tweet_id']}")

    if "created_at" in pinned_tweet and "text" in pinned_tweet:
        tweet_created_at = datetime.datetime.strptime(pinned_tweet["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        user_report_entries.append(
            f"Pinned tweet information: Pinned tweet created at "
            f"{tweet_created_at.strftime('%B %d, %Y at %H:%M:%S')} "
            f"with text: '{pinned_tweet['text']}'"
        )

    return "\n".join(user_report_entries)


def _handle_http_error(response: requests.Response) -> str:
    r"""Handles the HTTP response by checking the status code and
    returning an appropriate message if there is an error.

    Args:
        response (requests.Response): The HTTP response to handle.

    Returns:
        str: A string describing the error, if any. If there is no error,
            the function returns an "Unexpected Exception" message.

    Reference:
        https://github.com/tweepy/tweepy/blob/master/tweepy/client.py#L64
    """
    if response.status_code in responses:
        # For 5xx server errors, return "Twitter Server Error"
        if 500 <= response.status_code < 600:
            return "Twitter Server Error"
        else:
            error_message = responses[response.status_code] + " Error"
            return error_message
    elif not 200 <= response.status_code < 300:
        return "HTTP Exception"
    else:
        return "Unexpected Exception"


class TwitterToolkit(BaseToolkit):
    r"""A class representing a toolkit for Twitter operations.

    This class provides methods for creating a tweet, deleting a tweet, and
    getting the authenticated user's profile information.

    References:
        https://developer.x.com/en/portal/dashboard

    Notes:
        To use this toolkit, you need to set the following environment
        variables:
        - TWITTER_CONSUMER_KEY: The consumer key for the Twitter API.
        - TWITTER_CONSUMER_SECRET: The consumer secret for the Twitter API.
        - TWITTER_ACCESS_TOKEN: The access token for the Twitter API.
        - TWITTER_ACCESS_TOKEN_SECRET: The access token secret for the Twitter
            API.
    """

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """
        return [
            FunctionTool(create_tweet),
            FunctionTool(delete_tweet),
            FunctionTool(get_my_user_profile),
            FunctionTool(get_user_by_username),
        ]
