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
import subprocess
from typing import Tuple

class DeveloperToolkit:
    """A comprehensive toolkit for a developer agent that can inspect, modify,
    and upgrade its own codebase.
    """

    def _run_command(self, command: list[str]) -> Tuple[int, str, str]:
        """Helper to run a shell command and capture output."""
        # Security Guardrail: Restrict shell script execution to the `scripts` dir
        if command[0] == "bash" or command[0].endswith(".sh"):
            script_path = os.path.abspath(command[1])
            allowed_dir = os.path.abspath("scripts")
            if not script_path.startswith(allowed_dir):
                return -1, "", f"Error: Security policy prevents execution of scripts outside the 'scripts/' directory."

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            return process.returncode, process.stdout, process.stderr
        except FileNotFoundError:
            return -1, "", f"Error: Command '{command[0]}' not found."
        except Exception as e:
            return -1, "", f"An unexpected error occurred: {e}"

    def list_files(self, directory: str = ".") -> str:
        """Recursively lists all files and directories within a given
        directory.

        Args:
            directory (str, optional): The directory to list. Defaults to the
                                     current directory.

        Returns:
            str: A string representing the directory tree.
        """
        if not os.path.isdir(directory):
            return f"Error: Directory '{directory}' not found."

        tree = []
        for root, dirs, files in os.walk(directory):
            level = root.replace(directory, '').count(os.sep)
            indent = ' ' * 4 * (level)
            tree.append(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                tree.append(f"{sub_indent}{f}")

        return "\n".join(tree)

    def read_file(self, file_path: str) -> str:
        """Reads and returns the content of a specified file.

        Args:
            file_path (str): The path to the file to read.

        Returns:
            str: The content of the file, or an error message.
        """
        if not os.path.exists(file_path):
            return f"Error: File not found at '{file_path}'."
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(self, file_path: str, content: str) -> str:
        """Writes content to a specified file, overwriting it if it exists.
        For security, this tool can only write to files within the 'owl',
        'examples', and 'scripts' directories.

        Args:
            file_path (str): The path to the file to write to.
            content (str): The new content to write to the file.

        Returns:
            str: A success or error message.
        """
        # Security Guardrail: Prevent writing to arbitrary locations
        allowed_dirs = ["owl", "examples", "scripts"]
        working_dir = os.getcwd()

        # Resolve the absolute path of the target file
        absolute_path = os.path.abspath(file_path)

        # Check if the resolved path is within one of the allowed directories
        is_safe = False
        for allowed_dir in allowed_dirs:
            allowed_path = os.path.join(working_dir, allowed_dir)
            if absolute_path.startswith(allowed_path):
                is_safe = True
                break

        if not is_safe:
            return (
                "Error: For security reasons, file writing is restricted to "
                "the 'owl', 'examples', and 'scripts' directories."
            )

        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote content to '{file_path}'."
        except Exception as e:
            return f"Error writing file: {e}"

    def check_for_git_updates(self) -> str:
        """Checks for new updates in the remote git repository.

        Returns:
            str: A message indicating if updates are available or not.
        """
        print("Checking for git updates...")
        returncode, stdout, stderr = self._run_command(["git", "fetch"])
        if returncode != 0:
            return f"Error running 'git fetch': {stderr}"

        returncode, stdout, stderr = self._run_command(["git", "status", "-uno"])
        if returncode != 0:
            return f"Error running 'git status': {stderr}"

        if "Your branch is up to date" in stdout:
            return "No new updates found."
        elif "Your branch is behind" in stdout:
            return "Updates available."
        else:
            return f"Could not determine git status. Output:\n{stdout}"

    def run_tests(self) -> str:
        """Runs the test suite to verify the application's integrity.

        Returns:
            str: A summary of the test results, indicating pass or fail.
        """
        print("Running tests...")
        returncode, stdout, stderr = self._run_command(["bash", "scripts/test.sh"])
        result = f"Test Script Exit Code: {returncode}\n---\nSTDOUT:\n{stdout}\n---\nSTDERR:\n{stderr}"
        if returncode == 0:
            result += "\n---\nRESULT: Tests PASSED."
        else:
            result += "\n---\nRESULT: Tests FAILED."
        return result

    def run_upgrade_from_git(self) -> str:
        """
        Runs the full, safe upgrade process from the git repository.
        This involves backing up, upgrading, testing, and restoring on failure.

        Returns:
            str: A detailed log of the entire upgrade process and its outcome.
        """
        print("Starting safe git upgrade process...")

        # 1. Backup
        backup_code, backup_out, backup_err = self._run_command(["bash", "scripts/backup.sh"])
        if backup_code != 0:
            return f"Upgrade failed at backup step. Error:\n{backup_err}"

        # 2. Upgrade
        upgrade_code, upgrade_out, upgrade_err = self._run_command(["bash", "scripts/upgrade.sh"])
        if upgrade_code != 0:
            return f"Upgrade failed at git pull step. Error:\n{upgrade_err}"

        # 3. Test
        test_code, test_out, test_err = self._run_command(["bash", "scripts/test.sh"])

        final_report = f"BACKUP LOG:\n{backup_out}\n{backup_err}\n\n"
        final_report += f"UPGRADE LOG:\n{upgrade_out}\n{upgrade_err}\n\n"
        final_report += f"TEST LOG:\n{test_out}\n{test_err}\n\n"

        if test_code == 0:
            final_report += "FINAL STATUS: Upgrade successful and tests passed."
        else:
            # 4. Restore on failure
            final_report += "TESTS FAILED. Restoring from backup...\n"
            restore_code, restore_out, restore_err = self._run_command(["bash", "scripts/restore.sh"])
            final_report += f"RESTORE LOG:\n{restore_out}\n{restore_err}\n\n"
            if restore_code == 0:
                final_report += "FINAL STATUS: Upgrade failed. Code has been restored from backup."
            else:
                final_report += "CRITICAL ERROR: Upgrade failed AND restore failed. Manual intervention required."

        return final_report
