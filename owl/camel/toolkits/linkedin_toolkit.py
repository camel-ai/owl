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
import os
from http import HTTPStatus
from typing import List

import requests

from camel.toolkits import FunctionTool
from camel.toolkits.base import BaseToolkit
from camel.utils import handle_http_error

LINKEDIN_POST_LIMIT = 1300


class LinkedInToolkit(BaseToolkit):
    r"""A class representing a toolkit for LinkedIn operations.

    This class provides methods for creating a post, deleting a post, and
    retrieving the authenticated user's profile information.
    """

    def __init__(self):
        self._access_token = self._get_access_token()

    def create_post(self, text: str) -> dict:
        r"""Creates a post on LinkedIn for the authenticated user.

        Args:
            text (str): The content of the post to be created.

        Returns:
            dict: A dictionary containing the post ID and the content of
                the post. If the post creation fails, the values will be None.

        Raises:
            Exception: If the post creation fails due to
                       an error response from LinkedIn API.
        """
        url = "https://api.linkedin.com/v2/ugcPosts"
        urn = self.get_profile(include_id=True)

        headers = {
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }

        post_data = {
            "author": urn["id"],
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        response = requests.post(url, headers=headers, data=json.dumps(post_data))
        if response.status_code == 201:
            post_response = response.json()
            post_id = post_response.get("id", None)  # Get the ID of the post
            return {"Post ID": post_id, "Text": text}
        else:
            raise Exception(
                f"Failed to create post. Status code: {response.status_code}, " f"Response: {response.text}"
            )

    def delete_post(self, post_id: str) -> str:
        r"""Deletes a LinkedIn post with the specified ID
        for an authorized user.

        This function sends a DELETE request to the LinkedIn API to delete
        a post with the specified ID. Before sending the request, it
        prompts the user to confirm the deletion.

        Args:
            post_id (str): The ID of the post to delete.

        Returns:
            str: A message indicating the result of the deletion. If the
                deletion was successful, the message includes the ID of the
                deleted post. If the deletion was not successful, the message
                includes an error message.

        Reference:
            https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/ugc-post-api
        """
        print("You are going to delete a LinkedIn post " f"with the following ID: {post_id}")

        confirm = input("Are you sure you want to delete this post? (yes/no): ")
        if confirm.lower() != "yes":
            return "Execution cancelled by the user."

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        response = requests.delete(
            f"https://api.linkedin.com/v2/ugcPosts/{post_id}",
            headers=headers,
        )

        if response.status_code != HTTPStatus.NO_CONTENT:
            error_type = handle_http_error(response)
            return f"Request returned a(n) {error_type!s}: " f"{response.status_code!s} {response.text}"

        return f"Post deleted successfully. Post ID: {post_id}."

    def get_profile(self, include_id: bool = False) -> dict:
        r"""Retrieves the authenticated user's LinkedIn profile info.

        This function sends a GET request to the LinkedIn API to retrieve the
        authenticated user's profile information. Optionally, it also returns
        the user's LinkedIn ID.

        Args:
            include_id (bool): Whether to include the LinkedIn profile ID in
                the response.

        Returns:
            dict: A dictionary containing the user's LinkedIn profile
                information. If `include_id` is True, the dictionary will also
                include the profile ID.

        Raises:
            Exception: If the profile retrieval fails due to an error response
                from LinkedIn API.
        """
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Connection": "Keep-Alive",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        response = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers=headers,
        )

        if response.status_code != HTTPStatus.OK:
            raise Exception(
                f"Failed to retrieve profile. "
                f"Status code: {response.status_code}, "
                f"Response: {response.text}"
            )

        json_response = response.json()

        locale = json_response.get("locale", {})
        country = locale.get("country", "N/A")
        language = locale.get("language", "N/A")

        profile_report = {
            "Country": country,
            "Language": language,
            "First Name": json_response.get("given_name"),
            "Last Name": json_response.get("family_name"),
            "Email": json_response.get("email"),
        }

        if include_id:
            profile_report["id"] = f"urn:li:person:{json_response['sub']}"

        return profile_report

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """
        return [
            FunctionTool(self.create_post),
            FunctionTool(self.delete_post),
            FunctionTool(self.get_profile),
        ]

    def _get_access_token(self) -> str:
        r"""Fetches the access token required for making LinkedIn API requests.

        Returns:
            str: The OAuth 2.0 access token or warming message if the
                environment variable `LINKEDIN_ACCESS_TOKEN` is not set or is
                empty.

        Reference:
            You can apply for your personal LinkedIn API access token through
            the link below:
            https://www.linkedin.com/developers/apps
        """
        token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        if not token:
            return "Access token not found. Please set LINKEDIN_ACCESS_TOKEN."
        return token
