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
import subprocess
import os
from typing import Tuple

class SystemToolkit:
    """A toolkit for performing system-level operations like backup, upgrade,
    and testing.
    """

    def _run_script(self, script_name: str) -> Tuple[int, str, str]:
        """A helper function to run a shell script and capture its output."""
        script_path = os.path.join("scripts", script_name)
        if not os.path.exists(script_path):
            return -1, "", f"Error: Script not found at {script_path}"

        try:
            process = subprocess.run(
                ["bash", script_path],
                capture_output=True,
                text=True,
                check=False,  # Do not raise exception on non-zero exit codes
            )
            stdout = process.stdout
            stderr = process.stderr
            return process.returncode, stdout, stderr
        except Exception as e:
            return -1, "", f"An unexpected error occurred: {e}"

    def backup(self) -> str:
        """Creates a backup of the current codebase by running the backup.sh
        script.

        Returns:
            str: The output of the backup script, including stdout and stderr.
        """
        returncode, stdout, stderr = self._run_script("backup.sh")
        return f"Backup Script Exit Code: {returncode}\n---\nSTDOUT:\n{stdout}\n---\nSTDERR:\n{stderr}"

    def upgrade(self) -> str:
        """Attempts to upgrade the codebase by running the upgrade.sh script,
        which pulls the latest changes from git.

        Returns:
            str: The output of the upgrade script, including stdout and stderr.
        """
        returncode, stdout, stderr = self._run_script("upgrade.sh")
        return f"Upgrade Script Exit Code: {returncode}\n---\nSTDOUT:\n{stdout}\n---\nSTDERR:\n{stderr}"

    def test(self) -> str:
        """Runs a smoke test on the codebase by executing the test.sh script.

        Returns:
            str: The output of the test script, including a clear statement
                 of whether the test passed or failed based on the exit code.
        """
        returncode, stdout, stderr = self._run_script("test.sh")
        result = f"Test Script Exit Code: {returncode}\n---\nSTDOUT:\n{stdout}\n---\nSTDERR:\n{stderr}"
        if returncode == 0:
            result += "\n---\nRESULT: Smoke test PASSED."
        else:
            result += "\n---\nRESULT: Smoke test FAILED."
        return result

    def restore(self) -> str:
        """Restores the codebase from the backup by running the restore.sh
        script.

        Returns:
            str: The output of the restore script, including stdout and stderr.
        """
        returncode, stdout, stderr = self._run_script("restore.sh")
        return f"Restore Script Exit Code: {returncode}\n---\nSTDOUT:\n{stdout}\n---\nSTDERR:\n{stderr}"
