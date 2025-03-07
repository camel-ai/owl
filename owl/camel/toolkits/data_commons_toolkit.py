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
from typing import Any, Dict, List, Optional, Union

from camel.toolkits.base import BaseToolkit

logger = logging.getLogger(__name__)


class DataCommonsToolkit(BaseToolkit):
    r"""A class representing a toolkit for Data Commons.

    This class provides methods for querying and retrieving data from the
    Data Commons knowledge graph. It includes functionality for:
    - Executing SPARQL queries
    - Retrieving triples associated with nodes
    - Fetching statistical time series data
    - Analyzing property labels and values
    - Retrieving places within a given place type
    - Obtaining statistical values for specific variables and locations

    All the data are grabbed from the knowledge graph of Data Commons.
    Refer to https://datacommons.org/browser/ for more details.
    """

    @staticmethod
    def query_data_commons(
        query_string: str,
    ) -> Optional[List[Dict[str, Any]]]:
        r"""Query the Data Commons knowledge graph using SPARQL.

        Args:
            query_string (str): A SPARQL query string.

        Returns:
            Optional[List[Dict[str, Any]]]: A list of dictionaries, each
                representing a node matching the query conditions if success,
                (default: :obj:`None`) otherwise.

        Note:
        - Only supports a limited subset of SPARQL functionality (ORDER BY,
          DISTINCT, LIMIT).
        - Each variable in the query should have a 'typeOf' condition.
        - The Python SPARQL library currently only supports the V1 version
          of the API.

        Reference:
            https://docs.datacommons.org/api/python/query.html
        """
        import datacommons

        try:
            results = datacommons.query(query_string)

            processed_results = [{key: value for key, value in row.items()} for row in results]

            return processed_results

        except Exception as e:
            logger.error(f"An error occurred while querying Data Commons: {e!s}")
            return None

    @staticmethod
    def get_triples(dcids: Union[str, List[str]], limit: int = 500) -> Optional[Dict[str, List[tuple]]]:
        r"""Retrieve triples associated with nodes.

        Args:
            dcids (Union[str, List[str]]): A single DCID or a list of DCIDs
                to query.
            limit (int): The maximum number of triples per
                combination of property and type. (default: :obj:`500`)

        Returns:
            Optional[Dict[str, List[tuple]]]: A dictionary where keys are
                DCIDs and values are lists of associated triples if success,
                (default: :obj:`None`) otherwise.

        Note:
        - The function will raise a ValueError if any of the required
          arguments are missing.
        - The function will raise a TypeError if the dcids are not a string
          or a list of strings.
        - The function will raise a ValueError if the limit is not between
          1 and 500.
        - The function will raise a KeyError if one or more of the provided
          DCIDs do not exist in the Data Commons knowledge graph.
        - The function will raise an Exception if an unexpected error occurs.

        Reference:
            https://docs.datacommons.org/api/python/triple.html
        """
        import datacommons

        try:
            result = datacommons.get_triples(dcids, limit)
            return result

        except Exception as e:
            logger.error(f"An error occurred: {e!s}")
            return None

    @staticmethod
    def get_stat_time_series(
        place: str,
        stat_var: str,
        measurement_method: Optional[str] = None,
        observation_period: Optional[str] = None,
        unit: Optional[str] = None,
        scaling_factor: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        r"""Retrieve statistical time series for a place.

        Args:
            place (str): The dcid of the Place to query for.
            stat_var (str): The dcid of the StatisticalVariable.
            measurement_method (str, optional): The technique used for
                measuring a statistical variable. (default: :obj:`None`)
            observation_period (str, optional): The time period over which an
                observation is made. (default: :obj:`None`)
            scaling_factor (str, optional): Property of statistical variables
                indicating factor by which a measurement is multiplied to fit
                a certain format. (default: :obj:`None`)
            unit (str, optional): The unit of measurement. (default:
                :obj:`None`)

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the statistical
                time series data if success, (default: :obj:`None`) otherwise.

        Reference:
            https://docs.datacommons.org/api/python/stat_series.html
        """
        import datacommons_pandas

        try:
            result = datacommons_pandas.get_stat_series(
                place,
                stat_var,
                measurement_method,
                observation_period,
                unit,
                scaling_factor,
            )
            return result
        except Exception as e:
            logger.error(f"An error occurred while querying Data Commons: {e!s}")
            return None

    @staticmethod
    def get_property_labels(dcids: Union[str, List[str]], out: bool = True) -> Optional[Dict[str, List[str]]]:
        r"""Retrieves and analyzes property labels for given DCIDs.

        Args:
            dcids (list): A list of Data Commons IDs (DCIDs) to analyze.
            out (bool): Direction of properties to retrieve. (default:
                :obj:`True`)

        Returns:
            Optional[Dict[str, List[str]]]: Analysis results for each DCID if
                success, (default: :obj:`None`) otherwise.

        Reference:
            https://docs.datacommons.org/api/python/property_label.html
        """
        import datacommons

        try:
            result = datacommons.get_property_labels(dcids, out=out)
            return result
        except Exception as e:
            logger.error(f"An error occurred while analyzing property labels: {e!s}")
            return None

    @staticmethod
    def get_property_values(
        dcids: Union[str, List[str]],
        prop: str,
        out: Optional[bool] = True,
        value_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        r"""Retrieves and analyzes property values for given DCIDs.

        Args:
            dcids (list): A list of Data Commons IDs (DCIDs) to analyze.
            prop (str): The property to analyze.
            value_type (str, optional): The type of the property value to
                filter by. Defaults to NONE. Only applicable if the value
                refers to a node.
            out (bool, optional): The label's direction. (default: :obj:`True`)
                (only returning response nodes directed towards the requested
                node). If set to False, will only return response nodes
                directed away from the request node. (default: :obj:`None`)
            limit (int, optional): (≤ 500) Maximum number of values returned
                per node. (default: :obj:`datacommons.utils._MAX_LIMIT`)

        Returns:
            Optional[Dict[str, Any]]: Analysis results for each DCID if
                success, (default: :obj:`None`) otherwise.

        Reference:
            https://docs.datacommons.org/api/python/property_value.html
        """
        import datacommons

        try:
            result = datacommons.get_property_values(dcids, prop, out, value_type, limit)
            return result

        except Exception as e:
            logger.error(f"An error occurred while analyzing property values: {e!s}")
            return None

    @staticmethod
    def get_places_in(dcids: list, place_type: str) -> Optional[Dict[str, Any]]:
        r"""Retrieves places within a given place type.

        Args:
            dcids (list): A list of Data Commons IDs (DCIDs) to analyze.
            place_type (str): The type of the place to filter by.

        Returns:
            Optional[Dict[str, Any]]: Analysis results for each DCID if
                success, (default: :obj:`None`) otherwise.

        Reference:
            https://docs.datacommons.org/api/python/place_in.html
        """
        import datacommons

        try:
            result = datacommons.get_places_in(dcids, place_type)
            return result

        except Exception as e:
            logger.error("An error occurred while retrieving places in a given place " f"type: {e!s}")
            return None

    @staticmethod
    def get_stat_value(
        place: str,
        stat_var: str,
        date: Optional[str] = None,
        measurement_method: Optional[str] = None,
        observation_period: Optional[str] = None,
        unit: Optional[str] = None,
        scaling_factor: Optional[str] = None,
    ) -> Optional[float]:
        r"""Retrieves the value of a statistical variable for a given place
        and date.

        Args:
            place (str): The DCID of the Place to query for.
            stat_var (str): The DCID of the StatisticalVariable.
            date (str, optional): The preferred date of observation in ISO
                8601 format. If not specified, returns the latest observation.
                (default: :obj:`None`)
            measurement_method (str, optional): The DCID of the preferred
                measurementMethod value. (default: :obj:`None`)
            observation_period (str, optional): The preferred observationPeriod
                value. (default: :obj:`None`)
            unit (str, optional): The DCID of the preferred unit value.
                (default: :obj:`None`)
            scaling_factor (str, optional): The preferred scalingFactor value.
                (default: :obj:`None`)

        Returns:
            Optional[float]: The value of the statistical variable for the
                given place and date if success, (default: :obj:`None`)
                otherwise.

        Reference:
            https://docs.datacommons.org/api/python/stat_value.html
        """
        import datacommons

        try:
            result = datacommons.get_stat_value(
                place,
                stat_var,
                date,
                measurement_method,
                observation_period,
                unit,
                scaling_factor,
            )
            return result

        except Exception as e:
            logger.error("An error occurred while retrieving the value of a " f"statistical variable: {e!s}")
            return None

    @staticmethod
    def get_stat_all(places: str, stat_vars: str) -> Optional[dict]:
        r"""Retrieves the value of a statistical variable for a given place
        and date.

        Args:
            places (str): The DCID IDs of the Place objects to query for.
                (Here DCID stands for Data Commons ID, the unique identifier
                assigned to all entities in Data Commons.)
            stat_vars (str): The dcids of the StatisticalVariables at
                https://datacommons.org/browser/StatisticalVariable

        Returns:
            Optional[dict]: A dictionary with the DCID of the place as the key
                and a list of tuples as the value if success, (default:
                :obj:`None`) otherwise.

        Reference:
            https://docs.datacommons.org/api/python/stat_all.html
        """
        import datacommons

        try:
            result = datacommons.get_stat_all(places, stat_vars)
            return result

        except Exception as e:
            logger.error("An error occurred while retrieving the value of a " f"statistical variable: {e!s}")
            return None
