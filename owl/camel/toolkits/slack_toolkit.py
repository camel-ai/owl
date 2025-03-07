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

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, List, Optional

from camel.toolkits.base import BaseToolkit

if TYPE_CHECKING:
    from ssl import SSLContext

    from slack_sdk import WebClient

from camel.toolkits import FunctionTool

logger = logging.getLogger(__name__)


class SlackToolkit(BaseToolkit):
    r"""A class representing a toolkit for Slack operations.

    This class provides methods for Slack operations such as creating a new
    channel, joining an existing channel, leaving a channel.
    """

    def _login_slack(
        self,
        slack_token: Optional[str] = None,
        ssl: Optional[SSLContext] = None,
    ) -> WebClient:
        r"""Authenticate using the Slack API.

        Args:
            slack_token (str, optional): The Slack API token.
                If not provided, it attempts to retrieve the token from
                the environment variable SLACK_BOT_TOKEN or SLACK_USER_TOKEN.
            ssl (SSLContext, optional): SSL context for secure connections.
                Defaults to `None`.

        Returns:
            WebClient: A WebClient object for interacting with Slack API.

        Raises:
            ImportError: If slack_sdk package is not installed.
            KeyError: If SLACK_BOT_TOKEN or SLACK_USER_TOKEN
                environment variables are not set.
        """
        try:
            from slack_sdk import WebClient
        except ImportError as e:
            raise ImportError(
                "Cannot import slack_sdk. Please install the package with \
                `pip install slack_sdk`."
            ) from e
        if not slack_token:
            slack_token = os.environ.get("SLACK_BOT_TOKEN") or os.environ.get("SLACK_USER_TOKEN")
            if not slack_token:
                raise KeyError("SLACK_BOT_TOKEN or SLACK_USER_TOKEN environment " "variable not set.")

        client = WebClient(token=slack_token, ssl=ssl)
        logger.info("Slack login successful.")
        return client

    def create_slack_channel(self, name: str, is_private: Optional[bool] = True) -> str:
        r"""Creates a new slack channel, either public or private.

        Args:
            name (str): Name of the public or private channel to create.
            is_private (bool, optional): Whether to create a private channel
                instead of a public one. Defaults to `True`.

        Returns:
            str: JSON string containing information about Slack
                channel created.

        Raises:
            SlackApiError: If there is an error during get slack channel
                information.
        """
        from slack_sdk.errors import SlackApiError

        try:
            slack_client = self._login_slack()
            response = slack_client.conversations_create(name=name, is_private=is_private)
            channel_id = response["channel"]["id"]
            response = slack_client.conversations_archive(channel=channel_id)
            return str(response)
        except SlackApiError as e:
            return f"Error creating conversation: {e.response['error']}"

    def join_slack_channel(self, channel_id: str) -> str:
        r"""Joins an existing Slack channel.

        Args:
            channel_id (str): The ID of the Slack channel to join.

        Returns:
            str: A confirmation message indicating whether join successfully
                or an error message.

        Raises:
            SlackApiError: If there is an error during get slack channel
                information.
        """
        from slack_sdk.errors import SlackApiError

        try:
            slack_client = self._login_slack()
            response = slack_client.conversations_join(channel=channel_id)
            return str(response)
        except SlackApiError as e:
            return f"Error creating conversation: {e.response['error']}"

    def leave_slack_channel(self, channel_id: str) -> str:
        r"""Leaves an existing Slack channel.

        Args:
            channel_id (str): The ID of the Slack channel to leave.

        Returns:
            str: A confirmation message indicating whether leave successfully
                or an error message.

        Raises:
            SlackApiError: If there is an error during get slack channel
                information.
        """
        from slack_sdk.errors import SlackApiError

        try:
            slack_client = self._login_slack()
            response = slack_client.conversations_leave(channel=channel_id)
            return str(response)
        except SlackApiError as e:
            return f"Error creating conversation: {e.response['error']}"

    def get_slack_channel_information(self) -> str:
        r"""Retrieve Slack channels and return relevant information in JSON
            format.

        Returns:
            str: JSON string containing information about Slack channels.

        Raises:
            SlackApiError: If there is an error during get slack channel
                information.
        """
        from slack_sdk.errors import SlackApiError

        try:
            slack_client = self._login_slack()
            response = slack_client.conversations_list()
            conversations = response["channels"]
            # Filtering conversations and extracting required information
            filtered_result = [
                {key: conversation[key] for key in ("id", "name", "created", "num_members")}
                for conversation in conversations
                if all(key in conversation for key in ("id", "name", "created", "num_members"))
            ]
            return json.dumps(filtered_result, ensure_ascii=False)
        except SlackApiError as e:
            return f"Error creating conversation: {e.response['error']}"

    def get_slack_channel_message(self, channel_id: str) -> str:
        r"""Retrieve messages from a Slack channel.

        Args:
            channel_id (str): The ID of the Slack channel to retrieve messages
                from.

        Returns:
            str: JSON string containing filtered message data.

        Raises:
            SlackApiError: If there is an error during get
                slack channel message.
        """
        from slack_sdk.errors import SlackApiError

        try:
            slack_client = self._login_slack()
            result = slack_client.conversations_history(channel=channel_id)
            messages = result["messages"]
            filtered_messages = [
                {key: message[key] for key in ("user", "text", "ts")}
                for message in messages
                if all(key in message for key in ("user", "text", "ts"))
            ]
            return json.dumps(filtered_messages, ensure_ascii=False)
        except SlackApiError as e:
            return f"Error retrieving messages: {e.response['error']}"

    def send_slack_message(
        self,
        message: str,
        channel_id: str,
        user: Optional[str] = None,
    ) -> str:
        r"""Send a message to a Slack channel.

        Args:
            message (str): The message to send.
            channel_id (str): The ID of the Slack channel to send message.
            user (Optional[str]): The user ID of the recipient.
                Defaults to `None`.

        Returns:
            str: A confirmation message indicating whether the message was sent
                successfully or an error message.

        Raises:
            SlackApiError: If an error occurs while sending the message.
        """
        from slack_sdk.errors import SlackApiError

        try:
            slack_client = self._login_slack()
            if user:
                response = slack_client.chat_postEphemeral(channel=channel_id, text=message, user=user)
            else:
                response = slack_client.chat_postMessage(channel=channel_id, text=message)
            return str(response)
        except SlackApiError as e:
            return f"Error creating conversation: {e.response['error']}"

    def delete_slack_message(
        self,
        time_stamp: str,
        channel_id: str,
    ) -> str:
        r"""Delete a message to a Slack channel.

        Args:
            time_stamp (str): Timestamp of the message to be deleted.
            channel_id (str): The ID of the Slack channel to delete message.

        Returns:
            str: A confirmation message indicating whether the message
                was delete successfully or an error message.

        Raises:
            SlackApiError: If an error occurs while sending the message.
        """
        from slack_sdk.errors import SlackApiError

        try:
            slack_client = self._login_slack()
            response = slack_client.chat_delete(channel=channel_id, ts=time_stamp)
            return str(response)
        except SlackApiError as e:
            return f"Error creating conversation: {e.response['error']}"

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """
        return [
            FunctionTool(self.create_slack_channel),
            FunctionTool(self.join_slack_channel),
            FunctionTool(self.leave_slack_channel),
            FunctionTool(self.get_slack_channel_information),
            FunctionTool(self.get_slack_channel_message),
            FunctionTool(self.send_slack_message),
            FunctionTool(self.delete_slack_message),
        ]
