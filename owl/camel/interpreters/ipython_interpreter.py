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

import queue
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from camel.interpreters.base import BaseInterpreter
from camel.interpreters.interpreter_error import InterpreterError

if TYPE_CHECKING:
    from jupyter_client import BlockingKernelClient, KernelManager

TIMEOUT = 30


class JupyterKernelInterpreter(BaseInterpreter):
    r"""A class for executing code strings in a Jupyter Kernel.

    Args:
        require_confirm (bool, optional): If `True`, prompt user before
            running code strings for security. Defaults to `True`.
        print_stdout (bool, optional): If `True`, print the standard
            output of the executed code. Defaults to `False`.
        print_stderr (bool, optional): If `True`, print the standard error
            of the executed code. Defaults to `True`.
    """

    def __init__(
        self,
        require_confirm: bool = True,
        print_stdout: bool = False,
        print_stderr: bool = True,
    ) -> None:
        self.require_confirm = require_confirm
        self.print_stdout = print_stdout
        self.print_stderr = print_stderr

        self.kernel_manager: Optional[KernelManager] = None
        self.client: Optional[BlockingKernelClient] = None

    def __del__(self) -> None:
        r"""Clean up the kernel and client."""

        if self.kernel_manager:
            self.kernel_manager.shutdown_kernel()
        if self.client:
            self.client.stop_channels()

    def _initialize_if_needed(self) -> None:
        r"""Initialize the kernel manager and client if they are not already
        initialized.
        """

        if self.kernel_manager is not None:
            return

        from jupyter_client.manager import start_new_kernel

        self.kernel_manager, self.client = start_new_kernel()

    @staticmethod
    def _clean_ipython_output(output: str) -> str:
        r"""Remove ANSI escape sequences from the output."""

        ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", output)

    def _execute(self, code: str, timeout: float) -> str:
        r"""Execute the code in the Jupyter kernel and return the result."""

        if not self.kernel_manager or not self.client:
            raise InterpreterError("Jupyter client is not initialized.")

        self.client.execute(code)
        outputs = []
        while True:
            try:
                msg = self.client.get_iopub_msg(timeout=timeout)
                msg_content = msg["content"]
                msg_type = msg.get("msg_type", None)

                if msg_content.get("execution_state", None) == "idle":
                    break

                if msg_type == "error":
                    print(msg_content.keys())
                    print(msg_content)
                    traceback = "\n".join(msg_content["traceback"])
                    outputs.append(traceback)
                elif msg_type == "stream":
                    outputs.append(msg_content["text"])
                elif msg_type in ["execute_result", "display_data"]:
                    outputs.append(msg_content["data"]["text/plain"])
                    if "image/png" in msg_content["data"]:
                        outputs.append(
                            f"\n![image](data:image/png;base64," f"{msg_content['data']['image/png']})\n"
                        )
            except queue.Empty:
                outputs.append("Time out")
                break
            except Exception as e:
                outputs.append(f"Exception occurred: {e!s}")
                break

        exec_result = "\n".join(outputs)
        return self._clean_ipython_output(exec_result)

    def run(self, code: str, code_type: str) -> str:
        r"""Executes the given code in the Jupyter kernel.

        Args:
            code (str): The code string to execute.
            code_type (str): The type of code to execute (e.g., 'python',
                'bash').

        Returns:
            str: A string containing the captured result of the
                executed code.

        Raises:
            InterpreterError: If there is an error when doing code execution.
        """
        self._initialize_if_needed()

        if code_type == "bash":
            code = f"%%bash\n({code})"
        try:
            result = self._execute(code, timeout=TIMEOUT)
        except Exception as e:
            raise InterpreterError(f"Execution failed: {e!s}")

        return result

    def supported_code_types(self) -> List[str]:
        r"""Provides supported code types by the interpreter.

        Returns:
            List[str]: Supported code types.
        """
        return ["python", "bash"]

    def update_action_space(self, action_space: Dict[str, Any]) -> None:
        r"""Updates the action space for the interpreter.

        Args:
            action_space (Dict[str, Any]): A dictionary representing the
                new or updated action space.

        Raises:
            RuntimeError: Always raised because `JupyterKernelInterpreter`
                does not support updating the action space.
        """
        raise RuntimeError("SubprocessInterpreter doesn't support " "`action_space`.")
