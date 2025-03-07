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
import os
from typing import Dict, List, Literal, Optional, Union

from camel.toolkits import FunctionTool
from camel.toolkits.base import BaseToolkit
from camel.utils import dependencies_required

logger = logging.getLogger(__name__)


class GithubToolkit(BaseToolkit):
    r"""A class representing a toolkit for interacting with GitHub
    repositories.

    This class provides methods for retrieving open issues, retrieving
        specific issues, and creating pull requests in a GitHub repository.

    Args:
        repo_name (str): The name of the GitHub repository.
        access_token (str, optional): The access token to authenticate with
            GitHub. If not provided, it will be obtained using the
            `get_github_access_token` method.
    """

    @dependencies_required("github")
    def __init__(self, repo_name: str, access_token: Optional[str] = None) -> None:
        r"""Initializes a new instance of the GitHubToolkit class.

        Args:
            repo_name (str): The name of the GitHub repository.
            access_token (str, optional): The access token to authenticate
                with GitHub. If not provided, it will be obtained using the
                `get_github_access_token` method.
        """
        from github import Auth, Github

        if access_token is None:
            access_token = self.get_github_access_token()

        self.github = Github(auth=Auth.Token(access_token))
        self.repo = self.github.get_repo(repo_name)

    def get_github_access_token(self) -> str:
        r"""Retrieve the GitHub access token from environment variables.

        Returns:
            str: A string containing the GitHub access token.

        Raises:
            ValueError: If the API key or secret is not found in the
                environment variables.
        """
        # Get `GITHUB_ACCESS_TOKEN` here: https://github.com/settings/tokens
        GITHUB_ACCESS_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN")

        if not GITHUB_ACCESS_TOKEN:
            raise ValueError(
                "`GITHUB_ACCESS_TOKEN` not found in environment variables. Get"
                " it here: `https://github.com/settings/tokens`."
            )
        return GITHUB_ACCESS_TOKEN

    def create_pull_request(
        self,
        file_path: str,
        new_content: str,
        pr_title: str,
        body: str,
        branch_name: str,
    ) -> str:
        r"""Creates a pull request.

        This function creates a pull request in specified repository, which
        updates a file in the specific path with new content. The pull request
        description contains information about the issue title and number.

        Args:
            file_path (str): The path of the file to be updated in the
                repository.
            new_content (str): The specified new content of the specified file.
            pr_title (str): The title of the issue that is solved by this pull
                request.
            body (str): The commit message for the pull request.
            branch_name (str): The name of the branch to create and submit the
                pull request from.

        Returns:
            str: A formatted report of whether the pull request was created
                successfully or not.
        """
        sb = self.repo.get_branch(self.repo.default_branch)
        self.repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sb.commit.sha)

        file = self.repo.get_contents(file_path)

        from github.ContentFile import ContentFile

        if isinstance(file, ContentFile):
            self.repo.update_file(file.path, body, new_content, file.sha, branch=branch_name)
            pr = self.repo.create_pull(
                title=pr_title,
                body=body,
                head=branch_name,
                base=self.repo.default_branch,
            )

            if pr is not None:
                return f"Title: {pr.title}\n" f"Body: {pr.body}\n"
            else:
                return "Failed to create pull request."
        else:
            raise ValueError("PRs with multiple files aren't supported yet.")

    def get_issue_list(self, state: Literal["open", "closed", "all"] = "all") -> List[Dict[str, object]]:
        r"""Retrieves all issues from the GitHub repository.

        Args:
            state (Literal["open", "closed", "all"]): The state of pull
                requests to retrieve. (default::obj: `all`)
                Options are:
                - "open": Retrieve only open pull requests.
                - "closed": Retrieve only closed pull requests.
                - "all": Retrieve all pull requests, regardless of state.

        Returns:
            List[Dict[str, object]]: A list of dictionaries where each
                dictionary contains the issue number and title.
        """
        issues_info = []
        issues = self.repo.get_issues(state=state)

        for issue in issues:
            issues_info.append({"number": issue.number, "title": issue.title})

        return issues_info

    def get_issue_content(self, issue_number: int) -> str:
        r"""Retrieves the content of a specific issue by its number.

        Args:
            issue_number (int): The number of the issue to retrieve.

        Returns:
            str: issues content details.
        """
        try:
            issue = self.repo.get_issue(number=issue_number)
            return issue.body
        except Exception as e:
            return f"can't get Issue number {issue_number}: {e!s}"

    def get_pull_request_list(self, state: Literal["open", "closed", "all"] = "all") -> List[Dict[str, object]]:
        r"""Retrieves all pull requests from the GitHub repository.

        Args:
            state (Literal["open", "closed", "all"]): The state of pull
                requests to retrieve. (default::obj: `all`)
                Options are:
                - "open": Retrieve only open pull requests.
                - "closed": Retrieve only closed pull requests.
                - "all": Retrieve all pull requests, regardless of state.

        Returns:
            list: A list of dictionaries where each dictionary contains the
                pull request number and title.
        """
        pull_requests_info = []
        pull_requests = self.repo.get_pulls(state=state)

        for pr in pull_requests:
            pull_requests_info.append({"number": pr.number, "title": pr.title})

        return pull_requests_info

    def get_pull_request_code(self, pr_number: int) -> List[Dict[str, str]]:
        r"""Retrieves the code changes of a specific pull request.

        Args:
            pr_number (int): The number of the pull request to retrieve.

        Returns:
            List[Dict[str, str]]: A list of dictionaries where each dictionary
                contains the file name and the corresponding code changes
                (patch).
        """
        # Retrieve the specific pull request
        pr = self.repo.get_pull(number=pr_number)

        # Collect the file changes from the pull request
        files_changed = []
        # Returns the files and their changes in the pull request
        files = pr.get_files()
        for file in files:
            files_changed.append(
                {
                    "filename": file.filename,
                    "patch": file.patch,  # The code diff or changes
                }
            )

        return files_changed

    def get_pull_request_comments(self, pr_number: int) -> List[Dict[str, str]]:
        r"""Retrieves the comments from a specific pull request.

        Args:
            pr_number (int): The number of the pull request to retrieve.

        Returns:
            List[Dict[str, str]]: A list of dictionaries where each dictionary
                contains the user ID and the comment body.
        """
        # Retrieve the specific pull request
        pr = self.repo.get_pull(number=pr_number)

        # Collect the comments from the pull request
        comments = []
        # Returns all the comments in the pull request
        for comment in pr.get_comments():
            comments.append({"user": comment.user.login, "body": comment.body})

        return comments

    def get_all_file_paths(self, path: str = "") -> List[str]:
        r"""Recursively retrieves all file paths in the GitHub repository.

        Args:
            path (str): The repository path to start the traversal from.
                empty string means starts from the root directory.
                (default::obj: `""`)

        Returns:
            List[str]: A list of file paths within the specified directory
                structure.
        """
        from github.ContentFile import ContentFile

        files: List[str] = []

        # Retrieves all contents of the current directory
        contents: Union[List[ContentFile], ContentFile] = self.repo.get_contents(path)

        if isinstance(contents, ContentFile):
            files.append(contents.path)
        else:
            for content in contents:
                if content.type == "dir":
                    # If it's a directory, recursively retrieve its file paths
                    files.extend(self.get_all_file_paths(content.path))
                else:
                    # If it's a file, add its path to the list
                    files.append(content.path)
        return files

    def retrieve_file_content(self, file_path: str) -> str:
        r"""Retrieves the content of a file from the GitHub repository.

        Args:
            file_path (str): The path of the file to retrieve.

        Returns:
            str: The decoded content of the file.
        """
        from github.ContentFile import ContentFile

        file_content = self.repo.get_contents(file_path)
        if isinstance(file_content, ContentFile):
            return file_content.decoded_content.decode()
        else:
            raise ValueError("PRs with multiple files aren't supported yet.")

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the functions
        in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects representing
                the functions in the toolkit.
        """
        return [
            FunctionTool(self.create_pull_request),
            FunctionTool(self.get_issue_list),
            FunctionTool(self.get_issue_content),
            FunctionTool(self.get_pull_request_list),
            FunctionTool(self.get_pull_request_code),
            FunctionTool(self.get_pull_request_comments),
            FunctionTool(self.get_all_file_paths),
            FunctionTool(self.retrieve_file_content),
        ]
