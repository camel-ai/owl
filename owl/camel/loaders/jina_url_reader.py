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
from typing import Any, Optional
from warnings import warn

from camel.types.enums import JinaReturnFormat

JINA_ENDPOINT = "https://r.jina.ai/"


class JinaURLReader:
    r"""URL Reader provided by Jina AI. The output is cleaner and more
    LLM-friendly than the URL Reader of UnstructuredIO. Can be configured to
    replace the UnstructuredIO URL Reader in the pipeline.

    Args:
        api_key (Optional[str], optional): The API key for Jina AI. If not
            provided, the reader will have a lower rate limit. Defaults to
            None.
        return_format (ReturnFormat, optional): The level of detail
            of the returned content, which is optimized for LLMs. For
            now screenshots are not supported. Defaults to
            ReturnFormat.DEFAULT.
        json_response (bool, optional): Whether to return the response
            in JSON format. Defaults to False.
        timeout (int, optional): The maximum time in seconds to wait for
            the page to be rendered. Defaults to 30.
        **kwargs (Any): Additional keyword arguments, including proxies,
            cookies, etc. It should align with the HTTP Header field and
            value pairs listed in the reference.

    References:
        https://jina.ai/reader
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        return_format: JinaReturnFormat = JinaReturnFormat.DEFAULT,
        json_response: bool = False,
        timeout: int = 30,
        **kwargs: Any,
    ) -> None:
        api_key = api_key or os.getenv("JINA_API_KEY")
        if not api_key:
            warn(
                "JINA_API_KEY not set. This will result in a low rate limit "
                "of Jina URL Reader. Get API key here: https://jina.ai/reader."
            )

        # if the following field not provided, it will be None
        api_field = f"Bearer {api_key}" if api_key else None
        json_field = "application/json" if json_response else None

        raw_headers = {
            "Authorization": api_field,
            "X-Return-Format": return_format.value,
            "Accept": json_field,
            "X-Timeout": str(timeout),
            **kwargs,
        }

        # eliminate None values
        self._headers = {k: v for k, v in raw_headers.items() if v}

    def read_content(self, url: str) -> str:
        r"""Reads the content of a URL and returns it as a string with
        given form.

        Args:
            url (str): The URL to read.

        Returns:
            str: The content of the URL.
        """

        import requests

        full_url = f"{JINA_ENDPOINT}{url}"
        try:
            resp = requests.get(full_url, headers=self._headers)
            resp.raise_for_status()
        except Exception as e:
            raise ValueError(f"Failed to read content from {url}: {e}") from e

        return resp.text
