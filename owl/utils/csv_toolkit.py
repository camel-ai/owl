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
import csv
import json
import os
from typing import List, Dict, Any

class CSVToolkit:
    """A toolkit for performing operations on CSV files."""

    def read_csv(self, file_path: str) -> str:
        """Reads the content of a CSV file and returns it as a JSON string
        representing a list of dictionaries.

        Args:
            file_path (str): The path to the CSV file.

        Returns:
            str: A JSON string of the CSV content, or an error message.
        """
        if not os.path.exists(file_path):
            return f"Error: File not found at '{file_path}'."

        try:
            with open(file_path, mode='r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                data = [row for row in reader]
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error reading CSV file: {e}"

    def write_csv(self, file_path: str, data: str) -> str:
        """Writes a list of dictionaries (provided as a JSON string) to a
        CSV file.

        Args:
            file_path (str): The path to the CSV file to be created.
            data (str): A JSON string representing a list of dictionaries.
                        Example: '[{"col1": "val1", "col2": "val2"}]'

        Returns:
            str: A success or error message.
        """
        try:
            list_of_dicts: List[Dict[str, Any]] = json.loads(data)
            if not isinstance(list_of_dicts, list) or not all(isinstance(d, dict) for d in list_of_dicts):
                return "Error: Data must be a JSON string of a list of dictionaries."

            if not list_of_dicts:
                return "Error: Data is empty, cannot write to CSV."

            headers = list_of_dicts[0].keys()
            with open(file_path, mode='w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(list_of_dicts)

            return f"Successfully wrote data to '{file_path}'."
        except json.JSONDecodeError:
            return "Error: Invalid JSON format in the provided data string."
        except Exception as e:
            return f"Error writing to CSV file: {e}"

    def query_csv(self, file_path: str, query: str) -> str:
        """Queries a CSV file based on a simple 'column=value' filter and
        returns the matching rows.

        Args:
            file_path (str): The path to the CSV file.
            query (str): A query string in the format 'column_name=value'.

        Returns:
            str: A JSON string of the filtered data, or an error message.
        """
        if not os.path.exists(file_path):
            return f"Error: File not found at '{file_path}'."

        try:
            column_to_query, value_to_match = query.split('=', 1)
        except ValueError:
            return "Error: Invalid query format. Please use 'column_name=value'."

        try:
            with open(file_path, mode='r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                filtered_data = [
                    row for row in reader if row.get(column_to_query) == value_to_match
                ]

            if not filtered_data:
                return "No matching rows found for the query."

            return json.dumps(filtered_data, indent=2)
        except Exception as e:
            return f"Error querying CSV file: {e}"
