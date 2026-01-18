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
import threading
import logging
from typing import List, Optional

import openai
from camel.models import OpenAICompatibleModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeyManager:
    """A class to manage a pool of API keys, including rotation and cooldown."""

    def __init__(self, key_env_var: str, cooldown_period: int = 300):
        """
        Initializes the KeyManager.

        Args:
            key_env_var (str): The name of the environment variable containing
                a comma-separated list of API keys.
            cooldown_period (int): The number of seconds a key should be in
                cooldown after a failure.
        """
        keys_str = os.getenv(key_env_var, "")
        self.keys: List[str] = [
            key.strip() for key in keys_str.split(",") if key.strip()
        ]
        if not self.keys:
            raise ValueError(
                f"No API keys found in environment variable '{key_env_var}'. "
                "Please provide a comma-separated list of keys."
            )

        self.cooldown_period = cooldown_period
        self.key_status: dict[str, float] = {
            key: 0.0 for key in self.keys
        }  # Key -> Cooldown end time
        self.current_key_index = 0
        self.lock = threading.Lock()

    def get_key(self) -> Optional[str]:
        """
        Gets the next available API key from the pool.

        It iterates through the keys, respecting cooldown periods.

        Returns:
            Optional[str]: An available API key, or None if all keys are
                           currently in cooldown.
        """
        with self.lock:
            # Try to find an available key starting from the current index
            for _ in range(len(self.keys)):
                key = self.keys[self.current_key_index]
                cooldown_end_time = self.key_status.get(key, 0.0)

                if time.time() >= cooldown_end_time:
                    # Key is available, move to the next index for next call
                    self.current_key_index = (self.current_key_index + 1) % len(
                        self.keys
                    )
                    return key

                # Key is in cooldown, try the next one
                self.current_key_index = (self.current_key_index + 1) % len(
                    self.keys
                )

            # If we complete the loop, all keys are in cooldown
            logger.warning("All API keys are currently in cooldown.")
            return None

    def set_cooldown(self, key: str):
        """
        Puts a specific key into a cooldown period after a failure.

        Args:
            key (str): The API key to put into cooldown.
        """
        with self.lock:
            cooldown_end_time = time.time() + self.cooldown_period
            self.key_status[key] = cooldown_end_time
            logger.info(
                f"Key '...{key[-4:]}' put on cooldown for "
                f"{self.cooldown_period} seconds."
            )

    def __repr__(self) -> str:
        return (
            f"KeyManager(keys={len(self.keys)}, "
            f"cooldown_period={self.cooldown_period}s)"
        )


class ResilientOpenAICompatibleModel(OpenAICompatibleModel):
    """
    A wrapper around OpenAICompatibleModel that adds resilience by using a
    pool of API keys and handling failures gracefully.
    """

    def __init__(self, key_manager: KeyManager, *args, **kwargs):
        """
        Initializes the resilient model.

        Args:
            key_manager (KeyManager): The key manager instance to use for
                API key rotation and cooldown.
            *args, **kwargs: Arguments to pass to the parent
                             OpenAICompatibleModel.
        """
        self.key_manager = key_manager
        # The 'api_key' will be managed dynamically, so we pop it from kwargs
        # to avoid it being set permanently in the parent class.
        kwargs.pop("api_key", None)
        super().__init__(*args, **kwargs)

    def _create_client(self, api_key: str):
        """Helper to create an OpenAI client with a specific key."""
        return openai.OpenAI(
            api_key=api_key,
            base_url=self.url,
            timeout=self.timeout,
            max_retries=0,  # We handle retries manually
        )

    def step(self, *args, **kwargs):
        """
        Overrides the parent 'step' method to add resilience.

        It attempts to make an API call with a key from the KeyManager.
        If the call fails due to authentication or rate limits, it puts the
        key on cooldown and retries with the next available key.
        """
        while True:  # Loop to retry with new keys
            current_key = self.key_manager.get_key()
            if current_key is None:
                raise RuntimeError(
                    "All API keys are in cooldown. Please wait or add more keys."
                )

            # Dynamically create the client with the current key
            self.client = self._create_client(current_key)

            try:
                # Attempt the API call using the parent's logic
                logger.info(f"Making API call with key '...{current_key[-4:]}'.")
                response = super().step(*args, **kwargs)
                return response
            except (
                openai.AuthenticationError,
                openai.RateLimitError,
                openai.PermissionDeniedError,
            ) as e:
                logger.warning(
                    f"API call failed for key '...{current_key[-4:]}'. "
                    f"Error: {e.__class__.__name__}. Putting key on cooldown."
                )
                self.key_manager.set_cooldown(current_key)
                # The loop will automatically try the next available key
            except Exception as e:
                # For other unexpected errors, re-raise the exception
                logger.error(f"An unexpected error occurred: {e}")
                raise e
