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

import io
import shlex
import tarfile
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional

from colorama import Fore

from camel.interpreters.base import BaseInterpreter
from camel.interpreters.interpreter_error import InterpreterError
from camel.logger import get_logger
from camel.utils import is_docker_running

if TYPE_CHECKING:
    from docker.models.containers import Container

logger = get_logger(__name__)


class DockerInterpreter(BaseInterpreter):
    r"""A class for executing code files or code strings in a docker container.

    This class handles the execution of code in different scripting languages
    (currently Python and Bash) within a docker container, capturing their
    stdout and stderr streams, and allowing user checking before executing code
    strings.

    Args:
        require_confirm (bool, optional): If `True`, prompt user before
            running code strings for security. Defaults to `True`.
        print_stdout (bool, optional): If `True`, print the standard
            output of the executed code. Defaults to `False`.
        print_stderr (bool, optional): If `True`, print the standard error
            of the executed code. Defaults to `True`.
    """

    _CODE_EXECUTE_CMD_MAPPING: ClassVar[Dict[str, str]] = {
        "python": "python {file_name}",
        "bash": "bash {file_name}",
    }

    _CODE_EXTENSION_MAPPING: ClassVar[Dict[str, str]] = {
        "python": "py",
        "bash": "sh",
    }

    _CODE_TYPE_MAPPING: ClassVar[Dict[str, str]] = {
        "python": "python",
        "py3": "python",
        "python3": "python",
        "py": "python",
        "shell": "bash",
        "bash": "bash",
        "sh": "bash",
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

        # lazy initialization of container
        self._container: Optional[Container] = None

    def __del__(self) -> None:
        r"""Destructor for the DockerInterpreter class.

        This method ensures that the Docker container is removed when the
        interpreter is deleted.
        """
        if self._container is not None:
            self._container.remove(force=True)

    def _initialize_if_needed(self) -> None:
        if self._container is not None:
            return

        if not is_docker_running():
            raise InterpreterError("Docker daemon is not running. Please install/start docker " "and try again.")

        import docker

        client = docker.from_env()
        self._container = client.containers.run(
            "python:3.10",
            detach=True,
            name=f"camel-interpreter-{uuid.uuid4()}",
            command="tail -f /dev/null",
        )

    def _create_file_in_container(self, content: str) -> Path:
        # get a random name for the file
        filename = str(uuid.uuid4())
        # create a tar in memory
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            tar.addfile(tarinfo, io.BytesIO(content.encode("utf-8")))
        tar_stream.seek(0)

        # copy the tar into the container
        if self._container is None:
            raise InterpreterError("Container is not initialized. Try running the code again.")
        self._container.put_archive("/tmp", tar_stream)
        return Path(f"/tmp/{filename}")

    def _run_file_in_container(
        self,
        file: Path,
        code_type: str,
    ) -> str:
        code_type = self._check_code_type(code_type)
        commands = shlex.split(self._CODE_EXECUTE_CMD_MAPPING[code_type].format(file_name=file.as_posix()))
        if self._container is None:
            raise InterpreterError("Container is not initialized. Try running the code again.")
        stdout, stderr = self._container.exec_run(
            commands,
            demux=True,
        ).output

        if self.print_stdout and stdout:
            print("======stdout======")
            print(Fore.GREEN + stdout.decode() + Fore.RESET)
            print("==================")
        if self.print_stderr and stderr:
            print("======stderr======")
            print(Fore.RED + stderr.decode() + Fore.RESET)
            print("==================")
        exec_result = f"{stdout.decode()}" if stdout else ""
        exec_result += f"(stderr: {stderr.decode()})" if stderr else ""
        return exec_result

    def run(
        self,
        code: str,
        code_type: str,
    ) -> str:
        r"""Executes the given code in the conatiner attached to the
        interpreter, and captures the stdout and stderr streams.

        Args:
            code (str): The code string to execute.
            code_type (str): The type of code to execute (e.g., 'python',
                'bash').

        Returns:
            str: A string containing the captured stdout and stderr of the
                executed code.

        Raises:
            InterpreterError: If the user declines to run the code, or the
                code type is unsupported, or there is an error in the docker
                API/container
        """
        import docker.errors

        code_type = self._check_code_type(code_type)

        # Print code for security checking
        if self.require_confirm:
            logger.info(f"The following {code_type} code will run on your " "computer: {code}")
            while True:
                choice = input("Running code? [Y/n]:").lower()
                if choice in ["y", "yes", "ye", ""]:
                    break
                elif choice not in ["no", "n"]:
                    continue
                raise InterpreterError(
                    "Execution halted: User opted not to run the code. "
                    "This choice stops the current operation and any "
                    "further code execution."
                )

        self._initialize_if_needed()

        try:
            temp_file_path = self._create_file_in_container(code)
            result = self._run_file_in_container(temp_file_path, code_type)
        except docker.errors.APIError as e:
            raise InterpreterError(
                f"Execution halted due to docker API error: {e.explanation}. "
                "This choice stops the current operation and any "
                "further code execution."
            ) from e
        except docker.errors.DockerException as e:
            raise InterpreterError(
                f"Execution halted due to docker exceptoin: {e}. "
                "This choice stops the current operation and any "
                "further code execution."
            ) from e
        return result

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
