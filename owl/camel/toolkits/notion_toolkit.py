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
from typing import List, Optional, cast

from camel.toolkits import FunctionTool
from camel.toolkits.base import BaseToolkit


def get_plain_text_from_rich_text(rich_text: List[dict]) -> str:
    r"""Extracts plain text from a list of rich text elements.

    Args:
        rich_text: A list of dictionaries representing rich text elements.
            Each dictionary should contain a key named "plain_text" with
            the plain text content.

    Returns:
        str: A string containing the combined plain text from all elements,
            joined together.
    """
    plain_texts = [element.get("plain_text", "") for element in rich_text]
    return "".join(plain_texts)


def get_media_source_text(block: dict) -> str:
    r"""Extracts the source URL and optional caption from a
    Notion media block.

    Args:
        block: A dictionary representing a Notion media block.

    Returns:
        A string containing the source URL and caption (if available),
            separated by a colon.
    """
    block_type = block.get("type", "Unknown Type")
    block_content = block.get(block_type, {})

    # Extract source URL based on available types
    source = (
        block_content.get("external", {}).get("url")
        or block_content.get("file", {}).get("url")
        or block_content.get("url", "[Missing case for media block types]: " + block_type)
    )

    # Extract caption if available
    caption_elements = block_content.get("caption", [])
    if caption_elements:
        caption = get_plain_text_from_rich_text(caption_elements)
        return f"{caption}: {source}"

    return source


class NotionToolkit(BaseToolkit):
    r"""A toolkit for retrieving information from the user's notion pages.

    Attributes:
        notion_token (Optional[str], optional): The notion_token used to
            interact with notion APIs.(default: :obj:`None`)
        notion_client (module): The notion module for interacting with
            the notion APIs.
    """

    def __init__(
        self,
        notion_token: Optional[str] = None,
    ) -> None:
        r"""Initializes the NotionToolkit.

        Args:
            notion_token (Optional[str], optional): The optional notion_token
                used to interact with notion APIs.(default: :obj:`None`)
        """
        from notion_client import Client

        self.notion_token = notion_token or os.environ.get("NOTION_TOKEN")
        self.notion_client = Client(auth=self.notion_token)

    def list_all_users(self) -> List[dict]:
        r"""Lists all users via the Notion integration.

        Returns:
            List[dict]: A list of user objects with type, name, and workspace.
        """
        all_users_info: List[dict] = []
        cursor = None

        while True:
            response = cast(
                dict,
                self.notion_client.users.list(start_cursor=cursor),
            )
            all_users_info.extend(response["results"])

            if not response["has_more"]:
                break

            cursor = response["next_cursor"]

        formatted_users = [
            {
                "type": user["type"],
                "name": user["name"],
                "workspace": user.get(user.get("type"), {}).get("workspace_name", ""),
            }
            for user in all_users_info
        ]

        return formatted_users

    def list_all_pages(self) -> List[dict]:
        r"""Lists all pages in the Notion workspace.

        Returns:
            List[dict]: A list of page objects with title and id.
        """
        all_pages_info: List[dict] = []
        cursor = None

        while True:
            response = cast(
                dict,
                self.notion_client.search(
                    filter={"property": "object", "value": "page"},
                    start_cursor=cursor,
                ),
            )
            all_pages_info.extend(response["results"])

            if not response["has_more"]:
                break

            cursor = response["next_cursor"]

        formatted_pages = [
            {
                "id": page.get("id"),
                "title": next(
                    (
                        title.get("text", {}).get("content")
                        for title in page["properties"].get("title", {}).get("title", [])
                        if title["type"] == "text"
                    ),
                    None,
                ),
            }
            for page in all_pages_info
        ]

        return formatted_pages

    def get_notion_block_text_content(self, block_id: str) -> str:
        r"""Retrieves the text content of a Notion block.

        Args:
            block_id (str): The ID of the Notion block to retrieve.

        Returns:
            str: The text content of a Notion block, containing all
                the sub blocks.
        """
        blocks: List[dict] = []
        cursor = None

        while True:
            response = cast(
                dict,
                self.notion_client.blocks.children.list(block_id=block_id, start_cursor=cursor),
            )
            blocks.extend(response["results"])

            if not response["has_more"]:
                break

            cursor = response["next_cursor"]

        block_text_content = " ".join([self.get_text_from_block(sub_block) for sub_block in blocks])

        return block_text_content

    def get_text_from_block(self, block: dict) -> str:
        r"""Extracts plain text from a Notion block based on its type.

        Args:
            block (dict): A dictionary representing a Notion block.

        Returns:
            str: A string containing the extracted plain text and block type.
        """
        # Get rich text for supported block types
        if block.get(block.get("type"), {}).get("rich_text"):
            # Empty string if it's an empty line
            text = get_plain_text_from_rich_text(block[block["type"]]["rich_text"])
        else:
            # Handle block types by case
            block_type = block.get("type")
            if block_type == "unsupported":
                text = "[Unsupported block type]"
            elif block_type == "bookmark":
                text = block["bookmark"]["url"]
            elif block_type == "child_database":
                text = block["child_database"]["title"]
                # Use other API endpoints for full database data
            elif block_type == "child_page":
                text = block["child_page"]["title"]
            elif block_type in ("embed", "video", "file", "image", "pdf"):
                text = get_media_source_text(block)
            elif block_type == "equation":
                text = block["equation"]["expression"]
            elif block_type == "link_preview":
                text = block["link_preview"]["url"]
            elif block_type == "synced_block":
                if block["synced_block"].get("synced_from"):
                    text = (
                        f"This block is synced with a block with ID: "
                        f"""
                        {block['synced_block']['synced_from']
                        [block['synced_block']['synced_from']['type']]}
                        """
                    )
                else:
                    text = "Source sync block that another" + "blocked is synced with."
            elif block_type == "table":
                text = f"Table width: {block['table']['table_width']}"
                # Fetch children for full table data
            elif block_type == "table_of_contents":
                text = f"ToC color: {block['table_of_contents']['color']}"
            elif block_type in ("breadcrumb", "column_list", "divider"):
                text = "No text available"
            else:
                text = "[Needs case added]"

        # Query children for blocks with children
        if block.get("has_children"):
            text += self.get_notion_block_text_content(block["id"])

        return text

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """
        return [
            FunctionTool(self.list_all_pages),
            FunctionTool(self.list_all_users),
            FunctionTool(self.get_notion_block_text_content),
        ]
