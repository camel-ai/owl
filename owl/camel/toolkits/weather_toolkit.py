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
from typing import List, Literal

from camel.toolkits.base import BaseToolkit
from camel.toolkits.function_tool import FunctionTool


class WeatherToolkit(BaseToolkit):
    r"""A class representing a toolkit for interacting with weather data.

    This class provides methods for fetching weather data for a given city
    using the OpenWeatherMap API.
    """

    def get_openweathermap_api_key(self) -> str:
        r"""Retrieve the OpenWeatherMap API key from environment variables.

        Returns:
            str: The OpenWeatherMap API key.

        Raises:
            ValueError: If the API key is not found in the environment
            variables.
        """
        # Get `OPENWEATHERMAP_API_KEY` here: https://openweathermap.org
        OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY")
        if not OPENWEATHERMAP_API_KEY:
            raise ValueError(
                "`OPENWEATHERMAP_API_KEY` not found in environment "
                "variables. Get `OPENWEATHERMAP_API_KEY` here: "
                "`https://openweathermap.org`."
            )
        return OPENWEATHERMAP_API_KEY

    def get_weather_data(
        self,
        city: str,
        temp_units: Literal["kelvin", "celsius", "fahrenheit"] = "kelvin",
        wind_units: Literal["meters_sec", "miles_hour", "knots", "beaufort"] = "meters_sec",
        visibility_units: Literal["meters", "miles"] = "meters",
        time_units: Literal["unix", "iso", "date"] = "unix",
    ) -> str:
        r"""Fetch and return a comprehensive weather report for a given city
        as a string. The report includes current weather conditions,
        temperature, wind details, visibility, and sunrise/sunset times,
        all formatted as a readable string.

        The function interacts with the OpenWeatherMap API to
        retrieve the data.

        Args:
            city (str): The name of the city for which the weather information
                is desired. Format "City, CountryCode" (e.g., "Paris, FR"
                for Paris, France). If the country code is not provided,
                the API will search for the city in all countries, which
                may yield incorrect results if multiple cities with the
                same name exist.
            temp_units (Literal['kelvin', 'celsius', 'fahrenheit']): Units for
                temperature. (default: :obj:`kelvin`)
            wind_units
                (Literal['meters_sec', 'miles_hour', 'knots', 'beaufort']):
                Units for wind speed. (default: :obj:`meters_sec`)
            visibility_units (Literal['meters', 'miles']): Units for visibility
                distance. (default: :obj:`meters`)
            time_units (Literal['unix', 'iso', 'date']): Format for sunrise and
                sunset times. (default: :obj:`unix`)

        Returns:
            str: A string containing the fetched weather data, formatted in a
                readable manner. If an error occurs, a message indicating the
                error will be returned instead.

        Example of return string:
            "Weather in Paris, FR: 15°C, feels like 13°C. Max temp: 17°C,
            Min temp : 12°C.
            Wind: 5 m/s at 270 degrees. Visibility: 10 kilometers.
            Sunrise at 05:46:05 (UTC), Sunset at 18:42:20 (UTC)."

        Note:
            Please ensure that the API key is valid and has permissions
                to access the weather data.
        """
        # NOTE: This tool may not work as expected since the input arguments
        # like `time_units` should be enum types which are not supported yet.

        try:
            import pyowm
        except ImportError:
            raise ImportError(
                "Please install `pyowm` first. You can install it by running " "`pip install pyowm`."
            )

        OPENWEATHERMAP_API_KEY = self.get_openweathermap_api_key()
        owm = pyowm.OWM(OPENWEATHERMAP_API_KEY)
        mgr = owm.weather_manager()

        try:
            observation = mgr.weather_at_place(city)
            weather = observation.weather

            # Temperature
            temperature = weather.temperature(temp_units)

            # Wind
            wind_data = observation.weather.wind(unit=wind_units)
            wind_speed = wind_data.get("speed")
            # 'N/A' if the degree is not available
            wind_deg = wind_data.get("deg", "N/A")

            # Visibility
            visibility_distance = observation.weather.visibility_distance
            visibility = (
                str(visibility_distance)
                if visibility_units == "meters"
                else str(observation.weather.visibility(unit="miles"))
            )

            # Sunrise and Sunset
            sunrise_time = str(weather.sunrise_time(timeformat=time_units))
            sunset_time = str(weather.sunset_time(timeformat=time_units))

            # Compile all the weather details into a report string
            weather_report = (
                f"Weather in {city}: "
                f"{temperature['temp']}°{temp_units.title()}, "
                f"feels like "
                f"{temperature['feels_like']}°{temp_units.title()}. "
                f"Max temp: {temperature['temp_max']}°{temp_units.title()}, "
                f"Min temp: {temperature['temp_min']}°{temp_units.title()}. "
                f"Wind: {wind_speed} {wind_units} at {wind_deg} degrees. "
                f"Visibility: {visibility} {visibility_units}. "
                f"Sunrise at {sunrise_time}, Sunset at {sunset_time}."
            )

            return weather_report

        except Exception as e:
            error_message = f"An error occurred while fetching weather data for {city}: " f"{e!s}."
            return error_message

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the
        functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects
                representing the functions in the toolkit.
        """
        return [
            FunctionTool(self.get_weather_data),
        ]
