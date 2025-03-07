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
import logging
import os
from typing import TYPE_CHECKING, List, Optional

from camel.utils import dependencies_required

if TYPE_CHECKING:
    from discord import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscordApp:
    r"""A class representing a Discord app that uses the `discord.py` library
    to interact with Discord servers.

    This bot can respond to messages in specific channels and only reacts to
    messages that mention the bot.

    Attributes:
        channel_ids (Optional[List[int]]): A list of allowed channel IDs. If
            provided, the bot will only respond to messages in these channels.
        token (Optional[str]): The Discord bot token used for authentication.
    """

    @dependencies_required("discord")
    def __init__(
        self,
        channel_ids: Optional[List[int]] = None,
        token: Optional[str] = None,
    ) -> None:
        r"""Initialize the DiscordApp instance by setting up the Discord client
        and event handlers.

        Args:
            channel_ids (Optional[List[int]]): A list of allowed channel IDs.
                The bot will only respond to messages in these channels if
                provided.
            token (Optional[str]): The Discord bot token for authentication.
                If not provided, the token will be retrieved from the
                environment variable `DISCORD_TOKEN`.

        Raises:
            ValueError: If the `DISCORD_TOKEN` is not found in environment
                variables.
        """
        self.token = token or os.getenv("DISCORD_TOKEN")
        self.channel_ids = channel_ids

        if not self.token:
            raise ValueError(
                "`DISCORD_TOKEN` not found in environment variables. Get it"
                " here: `https://discord.com/developers/applications`."
            )

        import discord

        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)

        # Register event handlers
        self._client.event(self.on_ready)
        self._client.event(self.on_message)

    async def start(self):
        r"""Asynchronously start the Discord bot using its token.

        This method starts the bot and logs into Discord asynchronously using
        the provided token. It should be awaited when used in an async
        environment.
        """
        await self._client.start(self.token)

    def run(self) -> None:
        r"""Start the Discord bot using its token.

        This method starts the bot and logs into Discord synchronously using
        the provided token. It blocks execution and keeps the bot running.
        """
        self._client.run(self.token)  # type: ignore[arg-type]

    async def on_ready(self) -> None:
        r"""Event handler that is called when the bot has successfully
        connected to the Discord server.

        When the bot is ready and logged into Discord, it prints a message
        displaying the bot's username.
        """
        logger.info(f"We have logged in as {self._client.user}")

    async def on_message(self, message: "Message") -> None:
        r"""Event handler for processing incoming messages.

        This method is called whenever a new message is received by the bot. It
        will ignore messages sent by the bot itself, only respond to messages
        in allowed channels (if specified), and only to messages that mention
        the bot.

        Args:
            message (discord.Message): The message object received from
                Discord.
        """
        # If the message author is the bot itself,
        # do not respond to this message
        if message.author == self._client.user:
            return

        # If allowed channel IDs are provided,
        # only respond to messages in those channels
        if self.channel_ids and message.channel.id not in self.channel_ids:
            return

        # Only respond to messages that mention the bot
        if not self._client.user or not self._client.user.mentioned_in(message):
            return

        logger.info(f"Received message: {message.content}")

    @property
    def client(self):
        return self._client
