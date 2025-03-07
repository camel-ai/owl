# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
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

import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any, ClassVar, Dict, List

from colorama import Fore

from camel.interpreters.base import BaseInterpreter
from camel.interpreters.interpreter_error import InterpreterError
from camel.logger import get_logger
import os

logger = get_logger(__name__)


class SubprocessInterpreter(BaseInterpreter):
    r"""SubprocessInterpreter is a class for executing code files or code
    strings in a subprocess.

    This class handles the execution of code in different scripting languages
    (currently Python, Bash, and Node.js) within a subprocess, capturing their
    stdout and stderr streams, and allowing user checking before executing code
    strings.

    Args:
        require_confirm (bool, optional): If True, prompt user before running
            code strings for security. (default: :obj:`True`)
        print_stdout (bool, optional): If True, print the standard output of
            the executed code. (default: :obj:`False`)
        print_stderr (bool, optional): If True, print the standard error of the
            executed code. (default: :obj:`True`)
    """

    _CODE_EXECUTE_CMD_MAPPING: ClassVar[Dict[str, str]] = {
        "python": "python {file_name}",
        "bash": "bash {file_name}",
        "node": "node {file_name}",
    }

    _CODE_EXTENSION_MAPPING: ClassVar[Dict[str, str]] = {
        "python": "py",
        "bash": "sh",
        "node": "js",
    }

    _CODE_TYPE_MAPPING: ClassVar[Dict[str, str]] = {
        "python": "python",
        "py3": "python",
        "python3": "python",
        "py": "python",
        "shell": "bash",
        "bash": "bash",
        "sh": "bash",
        "node": "node",
        "javascript": "node",
        "js": "node",
    }

    def __init__(
        self,
        require_confirm: bool = True,
        print_stdout: bool = False,
        print_stderr: bool = True,
    ) -> None:
        self.require_confirm = require_confirm
        self.print_stdout = print_stdout
        self.print_stderr = print_stderr

    def run_file(
        self,
        file: Path,
        code_type: str,
    ) -> str:
        r"""Executes a code file in a subprocess and captures its output.

        Args:
            file (Path): The path object of the file to run.
            code_type (str): The type of code to execute (e.g., 'python',
                'bash', 'node').

        Returns:
            str: A string containing the captured stdout and stderr of the
                executed code.

        Raises:
            RuntimeError: If the provided file path does not point to a file.
            InterpreterError: If the code type provided is not supported.
        """
        if not file.is_file():
            raise RuntimeError(f"{file} is not a file.")
        code_type = self._check_code_type(code_type)
        cmd = shlex.split(self._CODE_EXECUTE_CMD_MAPPING[code_type].format(file_name=str(file)))

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate()
        if self.print_stdout and stdout:
            print("======stdout======")
            print(Fore.GREEN + stdout + Fore.RESET)
            print("==================")
        if self.print_stderr and stderr:
            print("======stderr======")
            print(Fore.RED + stderr + Fore.RESET)
            print("==================")
        exec_result = f"{stdout}"
        exec_result += f"(stderr: {stderr})" if stderr else ""
        return exec_result

    def run(
        self,
        code: str,
        code_type: str,
    ) -> str:
        r"""Generates a temporary file with the given code, executes it, and
            deletes the file afterward.

        Args:
            code (str): The code string to execute.
            code_type (str): The type of code to execute (e.g., 'python',
                'bash', 'node').

        Returns:
            str: A string containing the captured stdout and stderr of the
                executed code.

        Raises:
            InterpreterError: If the user declines to run the code or if the
                code type is unsupported.
        """
        code_type = self._check_code_type(code_type)

        if self.require_confirm:
            logger.info(f"The following {code_type} code will run on your " "computer: {code}")
            while True:
                choice = input("Running code? [Y/n]:").lower()
                if choice in ["y", "yes", "ye", ""]:
                    break
                elif choice in ["no", "n"]:
                    raise InterpreterError(
                        "Execution halted: User opted not to run the code. "
                        "This choice stops the current operation and any "
                        "further code execution."
                    )

        temp_file_path = self._create_temp_file(code=code, extension=self._CODE_EXTENSION_MAPPING[code_type])

        result = self.run_file(temp_file_path, code_type)

        temp_file_path.unlink()
        return result

    def _create_temp_file(self, code: str, extension: str) -> Path:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=f".{extension}") as f:
            f.write(code)
            name = f.name
        return Path(name)

    # def _create_temp_file(self, code: str, extension: str) -> Path:
    #     # generate a random file name
    #     import datetime

    #     current_time = datetime.datetime.now().strftime("%d%H%M%S")

    #     temp_file_path = os.path.join("tmp", f"{current_time}.{extension}")
    #     with open(temp_file_path, "w", encoding='utf-8') as f:
    #         f.write(code)
    #     f.close()
    #     f.flush()
    #     breakpoint()
    #     return Path(temp_file_path)

    def _check_code_type(self, code_type: str) -> str:
        if code_type not in self._CODE_TYPE_MAPPING:
            raise InterpreterError(
                f"Unsupported code type {code_type}. Currently "
                f"`{self.__class__.__name__}` only supports "
                f"{', '.join(self._CODE_EXTENSION_MAPPING.keys())}."
            )
        return self._CODE_TYPE_MAPPING[code_type]

    def supported_code_types(self) -> List[str]:
        r"""Provides supported code types by the interpreter."""
        return list(self._CODE_EXTENSION_MAPPING.keys())

    def update_action_space(self, action_space: Dict[str, Any]) -> None:
        r"""Updates action space for *python* interpreter"""
        raise RuntimeError("SubprocessInterpreter doesn't support " "`action_space`.")
