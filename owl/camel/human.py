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
from typing import Any, Dict, Sequence

from colorama import Fore

from camel.messages import BaseMessage
from camel.responses import ChatAgentResponse
from camel.utils import print_text_animated


class Human:
    r"""A class representing a human user.

    Args:
        name (str): The name of the human user.
            (default: :obj:`"Kill Switch Engineer"`).
        logger_color (Any): The color of the menu options displayed to the
            user. (default: :obj:`Fore.MAGENTA`)

    Attributes:
        name (str): The name of the human user.
        logger_color (Any): The color of the menu options displayed to the
            user.
        input_button (str): The text displayed for the input button.
        kill_button (str): The text displayed for the kill button.
        options_dict (Dict[str, str]): A dictionary containing the options
            displayed to the user.
    """

    def __init__(
        self,
        name: str = "Kill Switch Engineer",
        logger_color: Any = Fore.MAGENTA,
    ) -> None:
        self.name = name
        self.logger_color = logger_color
        self.input_button = f"Input by {self.name}."
        self.kill_button = "Stop!!!"
        self.options_dict: Dict[str, str] = dict()

    def display_options(self, messages: Sequence[BaseMessage]) -> None:
        r"""Displays the options to the user.

        Args:
            messages (Sequence[BaseMessage]): A list of `BaseMessage` objects.

        Returns:
            None
        """
        options = [message.content for message in messages]
        options.append(self.input_button)
        options.append(self.kill_button)
        print_text_animated(
            self.logger_color + "\n> Proposals from "
            f"{messages[0].role_name} ({messages[0].role_type}). "
            "Please choose an option:\n"
        )
        for index, option in enumerate(options):
            print_text_animated(self.logger_color + f"\x1b[3mOption {index + 1}:\n{option}\x1b[0m\n")
            self.options_dict[str(index + 1)] = option

    def get_input(self) -> str:
        r"""Gets the input from the user.

        Returns:
            str: The user's input.
        """
        while True:
            human_input = input(self.logger_color + f"Please enter your choice ([1-{len(self.options_dict)}]): ")
            print("\n")
            if human_input in self.options_dict:
                break
            print_text_animated(self.logger_color + "\n> Invalid choice. Please try again.\n")

        return human_input

    def parse_input(self, human_input: str) -> str:
        r"""Parses the user's input and returns a `BaseMessage` object.

        Args:
            human_input (str): The user's input.

        Returns:
            content: A `str` object representing the user's input.
        """
        if self.options_dict[human_input] == self.input_button:
            content = input(self.logger_color + "Please enter your message: ")
        elif self.options_dict[human_input] == self.kill_button:
            exit(self.logger_color + f"Killed by {self.name}.")
        else:
            content = self.options_dict[human_input]

        return content

    def reduce_step(self, messages: Sequence[BaseMessage]) -> ChatAgentResponse:
        r"""Performs one step of the conversation by displaying options to the
        user, getting their input, and parsing their choice.

        Args:
            messages (Sequence[BaseMessage]): A list of BaseMessage objects.

        Returns:
            ChatAgentResponse: A `ChatAgentResponse` object representing the
                user's choice.
        """
        meta_chat_message = BaseMessage(
            role_name=messages[0].role_name,
            role_type=messages[0].role_type,
            meta_dict=messages[0].meta_dict,
            content="",
        )
        self.display_options(messages)
        human_input = self.get_input()
        content = self.parse_input(human_input)
        message = meta_chat_message.create_new_instance(content)
        return ChatAgentResponse(msgs=[message], terminated=False, info={})
