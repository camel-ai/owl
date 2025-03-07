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
from functools import wraps
from typing import Any, Callable, List, Optional, Union

from camel.toolkits.base import BaseToolkit
from camel.toolkits.function_tool import FunctionTool
from camel.utils import dependencies_required


def handle_googlemaps_exceptions(
    func: Callable[..., Any],
) -> Callable[..., Any]:
    r"""Decorator to catch and handle exceptions raised by Google Maps API
    calls.

    Args:
        func (Callable): The function to be wrapped by the decorator.

    Returns:
        Callable: A wrapper function that calls the wrapped function and
                handles exceptions.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # ruff: noqa: E501
            from googlemaps.exceptions import (  # type: ignore[import]
                ApiError,
                HTTPError,
                Timeout,
                TransportError,
            )
        except ImportError:
            raise ImportError(
                "Please install `googlemaps` first. You can install " "it by running `pip install googlemaps`."
            )

        try:
            return func(*args, **kwargs)
        except ApiError as e:
            return "An exception returned by the remote API. " f"Status: {e.status}, Message: {e.message}"
        except HTTPError as e:
            return "An unexpected HTTP error occurred. " f"Status Code: {e.status_code}"
        except Timeout:
            return "The request timed out."
        except TransportError as e:
            return "Something went wrong while trying to execute the " f"request. Details: {e.base_exception}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    return wrapper


def _format_offset_to_natural_language(offset: int) -> str:
    r"""Converts a time offset in seconds to a more natural language
    description using hours as the unit, with decimal places to represent
    minutes and seconds.

    Args:
        offset (int): The time offset in seconds. Can be positive,
            negative, or zero.

    Returns:
        str: A string representing the offset in hours, such as
            "+2.50 hours" or "-3.75 hours".
    """
    # Convert the offset to hours as a float
    hours = offset / 3600.0
    hours_str = f"{hours:+.2f} hour{'s' if abs(hours) != 1 else ''}"
    return hours_str


class GoogleMapsToolkit(BaseToolkit):
    r"""A class representing a toolkit for interacting with GoogleMaps API.
    This class provides methods for validating addresses, retrieving elevation,
    and fetching timezone information using the Google Maps API.
    """

    @dependencies_required("googlemaps")
    def __init__(self) -> None:
        import googlemaps

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "`GOOGLE_API_KEY` not found in environment variables. "
                "`GOOGLE_API_KEY` API keys are generated in the `Credentials` "
                "page of the `APIs & Services` tab of "
                "https://console.cloud.google.com/apis/credentials."
            )

        self.gmaps = googlemaps.Client(key=api_key)

    @handle_googlemaps_exceptions
    def get_address_description(
        self,
        address: Union[str, List[str]],
        region_code: Optional[str] = None,
        locality: Optional[str] = None,
    ) -> str:
        r"""Validates an address via Google Maps API, returns a descriptive
        summary. Validates an address using Google Maps API, returning a
        summary that includes information on address completion, formatted
        address, location coordinates, and metadata types that are true for
        the given address.

        Args:
            address (Union[str, List[str]]): The address or components to
                validate. Can be a single string or a list representing
                different parts.
            region_code (str, optional): Country code for regional restriction,
                helps narrow down results. (default: :obj:`None`)
            locality (str, optional): Restricts validation to a specific
                locality, e.g., "Mountain View". (default: :obj:`None`)

        Returns:
            str: Summary of the address validation results, including
                information on address completion, formatted address,
                geographical coordinates (latitude and longitude), and metadata
                types true for the address.
        """
        addressvalidation_result = self.gmaps.addressvalidation(
            [address],
            regionCode=region_code,
            locality=locality,
            enableUspsCass=False,
        )  # Always False as per requirements

        # Check if the result contains an error
        if "error" in addressvalidation_result:
            error_info = addressvalidation_result["error"]
            error_message = error_info.get("message", "An unknown error occurred")
            error_status = error_info.get("status", "UNKNOWN_STATUS")
            error_code = error_info.get("code", "UNKNOWN_CODE")
            return (
                f"Address validation failed with error: {error_message} "
                f"Status: {error_status}, Code: {error_code}"
            )

        # Assuming the successful response structure
        # includes a 'result' key
        result = addressvalidation_result["result"]
        verdict = result.get("verdict", {})
        address_info = result.get("address", {})
        geocode = result.get("geocode", {})
        metadata = result.get("metadata", {})

        # Construct the descriptive string
        address_complete = "Yes" if verdict.get("addressComplete", False) else "No"
        formatted_address = address_info.get("formattedAddress", "Not available")
        location = geocode.get("location", {})
        latitude = location.get("latitude", "Not available")
        longitude = location.get("longitude", "Not available")
        true_metadata_types = [key for key, value in metadata.items() if value]
        true_metadata_types_str = ", ".join(true_metadata_types) if true_metadata_types else "None"

        description = (
            f"Address completion status: {address_complete}. "
            f"Formatted address: {formatted_address}. "
            f"Location (latitude, longitude): ({latitude}, {longitude}). "
            f"Metadata indicating true types: {true_metadata_types_str}."
        )

        return description

    @handle_googlemaps_exceptions
    def get_elevation(self, lat: float, lng: float) -> str:
        r"""Retrieves elevation data for a given latitude and longitude.
        Uses the Google Maps API to fetch elevation data for the specified
        latitude and longitude. It handles exceptions gracefully and returns a
        description of the elevation, including its value in meters and the
        data resolution.

        Args:
            lat (float): The latitude of the location to query.
            lng (float): The longitude of the location to query.

        Returns:
            str: A description of the elevation at the specified location(s),
                including the elevation in meters and the data resolution. If
                elevation data is not available, a message indicating this is
                returned.
        """
        # Assuming gmaps is a configured Google Maps client instance
        elevation_result = self.gmaps.elevation((lat, lng))

        # Extract the elevation data from the first
        # (and presumably only) result
        if elevation_result:
            elevation = elevation_result[0]["elevation"]
            location = elevation_result[0]["location"]
            resolution = elevation_result[0]["resolution"]

            # Format the elevation data into a natural language description
            description = (
                f"The elevation at latitude {location['lat']}, "
                f"longitude {location['lng']} "
                f"is approximately {elevation:.2f} meters above sea level, "
                f"with a data resolution of {resolution:.2f} meters."
            )
        else:
            description = "Elevation data is not available for the given location."

        return description

    @handle_googlemaps_exceptions
    def get_timezone(self, lat: float, lng: float) -> str:
        r"""Retrieves timezone information for a given latitude and longitude.
        This function uses the Google Maps Timezone API to fetch timezone
        data for the specified latitude and longitude. It returns a natural
        language description of the timezone, including the timezone ID, name,
        standard time offset, daylight saving time offset, and the total
        offset from Coordinated Universal Time (UTC).

        Args:
            lat (float): The latitude of the location to query.
            lng (float): The longitude of the location to query.

        Returns:
            str: A descriptive string of the timezone information,
                including the timezone ID and name, standard time offset,
                daylight saving time offset, and total offset from UTC.
        """
        # Get timezone information
        timezone_dict = self.gmaps.timezone((lat, lng))

        # Extract necessary information
        dst_offset = timezone_dict["dstOffset"]  # Daylight Saving Time offset in seconds
        raw_offset = timezone_dict["rawOffset"]  # Standard time offset in seconds
        timezone_id = timezone_dict["timeZoneId"]
        timezone_name = timezone_dict["timeZoneName"]

        raw_offset_str = _format_offset_to_natural_language(raw_offset)
        dst_offset_str = _format_offset_to_natural_language(dst_offset)
        total_offset_seconds = dst_offset + raw_offset
        total_offset_str = _format_offset_to_natural_language(total_offset_seconds)

        # Create a natural language description
        description = (
            f"Timezone ID is {timezone_id}, named {timezone_name}. "
            f"The standard time offset is {raw_offset_str}. "
            f"Daylight Saving Time offset is {dst_offset_str}. "
            f"The total offset from Coordinated Universal Time (UTC) is "
            f"{total_offset_str}, including any Daylight Saving Time "
            f"adjustment if applicable. "
        )

        return description

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """
        return [
            FunctionTool(self.get_address_description),
            FunctionTool(self.get_elevation),
            FunctionTool(self.get_timezone),
        ]
