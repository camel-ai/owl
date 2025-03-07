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
import json
import logging
import os
import tarfile
import time
from functools import wraps
from pathlib import Path
from random import randint
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import requests
from pydantic import BaseModel
from tqdm import tqdm

from camel.runtime import BaseRuntime, TaskConfig
from camel.toolkits import FunctionTool

if TYPE_CHECKING:
    from docker.models.containers import Container

logger = logging.getLogger(__name__)


class DockerRuntime(BaseRuntime):
    r"""A class representing a runtime environment using Docker.
    This class automatically wraps functions to be executed
    in a Docker container.

    Args:
        image (str): The name of the Docker image to use for the runtime.
        port (int): The port number to use for the runtime API. (default::obj:
            `8000`)
        remove (bool): Whether to remove the container after stopping it. '
            (default::obj: `True`)
        kwargs (dict): Additional keyword arguments to pass to the
            Docker client.
    """

    def __init__(self, image: str, port: int = 8000, remove: bool = True, **kwargs):
        super().__init__()

        import docker

        self.client = docker.from_env()
        self.container: Optional[Container] = None

        api_path = Path(__file__).parent / "api.py"
        self.mounts: Dict[Path, Path] = dict()
        self.cp: Dict[Path, Path] = {api_path: Path("/home")}
        self.entrypoint: Dict[str, str] = dict()
        self.tasks: List[TaskConfig] = []

        self.docker_config = kwargs
        self.image = image
        self.port = port if port > 0 else randint(10000, 20000)
        self.remove = remove

        if not self.client.images.list(name=self.image):
            logger.warning(f"Image {self.image} not found. Pulling from Docker Hub.")
            self.client.images.pull(self.image)

    def mount(self, path: str, mount_path: str) -> "DockerRuntime":
        r"""Mount a local directory to the container.

        Args:
            path (str): The local path to mount.
            mount_path (str): The path to mount the local directory to in the
                container.

        Returns:
            DockerRuntime: The DockerRuntime instance.
        """

        _path, _mount_path = Path(path), Path(mount_path)
        if not _path.exists():
            raise FileNotFoundError(f"Path {_path} does not exist.")
        if not _path.is_dir():
            raise NotADirectoryError(f"Path {_path} is not a directory.")
        if not _path.is_absolute():
            raise ValueError(f"Path {_path} is not absolute.")
        if not _mount_path.is_absolute():
            raise ValueError(f"Mount path {_mount_path} is not absolute.")

        self.mounts[_path] = _mount_path
        return self

    def copy(self, source: str, dest: str) -> "DockerRuntime":
        r"""Copy a file or directory to the container.

        Args:
            source (str): The local path to the file.
            dest (str): The path to copy the file to in the container.

        Returns:
            DockerRuntime: The DockerRuntime instance.
        """
        _source, _dest = Path(source), Path(dest)
        if not _source.exists():
            raise FileNotFoundError(f"Source {_source} does not exist.")

        self.cp[_source] = _dest
        return self

    def add_task(
        self,
        task: TaskConfig,
    ) -> "DockerRuntime":
        r"""Add a task to run a command inside the container when building.
        Similar to `docker exec`.

        Args:
            task (TaskConfig): The configuration for the task.

        Returns:
            DockerRuntime: The DockerRuntime instance.
        """
        self.tasks.append(task)
        return self

    def exec_run(
        self,
        task: TaskConfig,
    ) -> Any:
        r"""Run a command inside this container. Similar to `docker exec`.

        Args:
            task (TaskConfig): The configuration for the task.

        Returns:
            (ExecResult): A tuple of (exit_code, output)
                exit_code: (int):
                    Exit code for the executed command or `None` if
                    either `stream` or `socket` is `True`.
                output: (generator, bytes, or tuple):
                    If `stream=True`, a generator yielding response chunks.
                    If `socket=True`, a socket object for the connection.
                    If `demux=True`, a tuple of two bytes: stdout and stderr.
                    A bytestring containing response data otherwise.

        Raises:
            RuntimeError: If the container does not exist.
        """
        if not self.container:
            raise RuntimeError("Container does not exist. Please build the container first.")

        return self.container.exec_run(**task.model_dump())

    def build(self, time_out: int = 15) -> "DockerRuntime":
        r"""Build the Docker container and start it.

        Args:
            time_out (int): The number of seconds to wait for the container to
                start. (default::obj: `15`)

        Returns:
            DockerRuntime: The DockerRuntime instance.
        """
        if self.container:
            logger.warning("Container already exists. Nothing to build.")
            return self

        import docker
        from docker.types import Mount

        mounts = []
        for local_path, mount_path in self.mounts.items():
            mounts.append(Mount(target=str(mount_path), source=str(local_path), type="bind"))

        container_params = {
            "image": self.image,
            "detach": True,
            "mounts": mounts,
            "command": "sleep infinity",
            **self.docker_config,
        }
        container_params["ports"] = {"8000/tcp": self.port}
        try:
            self.container = self.client.containers.create(**container_params)
        except docker.errors.APIError as e:
            raise RuntimeError(f"Failed to create container: {e!s}")

        try:
            self.container.start()
            # Wait for the container to start
            for _ in range(time_out):
                self.container.reload()
                logger.debug(f"Container status: {self.container.status}")
                if self.container.status == "running":
                    break
                time.sleep(1)

        except docker.errors.APIError as e:
            raise RuntimeError(f"Failed to start container: {e!s}")

        # Copy files to the container if specified
        for local_path, container_path in self.cp.items():
            logger.info(f"Copying {local_path} to {container_path}")
            try:
                with io.BytesIO() as tar_stream:
                    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                        tar.add(local_path, arcname=os.path.basename(local_path))
                    tar_stream.seek(0)
                    self.container.put_archive(str(container_path), tar_stream.getvalue())
            except docker.errors.APIError as e:
                raise RuntimeError(f"Failed to copy file {local_path} to container: {e!s}")

        if self.tasks:
            for task in tqdm(self.tasks, desc="Running tasks"):
                self.exec_run(task)

        exec = ["python3", "api.py", *list(self.entrypoint.values())]

        self.container.exec_run(exec, workdir="/home", detach=True)

        logger.info(f"Container started on port {self.port}")
        return self

    def add(  # type: ignore[override]
        self,
        funcs: Union[FunctionTool, List[FunctionTool]],
        entrypoint: str,
        redirect_stdout: bool = False,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> "DockerRuntime":
        r"""Add a function or list of functions to the runtime.

        Args:
            funcs (Union[FunctionTool, List[FunctionTool]]): The function or
                list of functions to add.
            entrypoint (str): The entrypoint for the function.
            redirect_stdout (bool): Whether to return the stdout of
                the function. (default::obj: `False`)
            arguments (Optional[Dict[str, Any]]): The arguments for the
                function. (default::obj: `None`)

        Returns:
            DockerRuntime: The DockerRuntime instance.
        """

        if not isinstance(funcs, list):
            funcs = [funcs]

        if arguments is not None:
            entrypoint += json.dumps(arguments)

        for func in funcs:
            inner_func = func.func

            # Create a wrapper that explicitly binds `func`
            @wraps(inner_func)
            def wrapper(*args, func=func, redirect_stdout=redirect_stdout, **kwargs):
                for key, value in kwargs.items():
                    if isinstance(value, BaseModel):
                        kwargs[key] = value.model_dump()

                resp = requests.post(
                    f"http://localhost:{self.port}/{func.get_function_name()}",
                    json=dict(
                        args=args,
                        kwargs=kwargs,
                        redirect_stdout=redirect_stdout,
                    ),
                )
                if resp.status_code != 200:
                    logger.error(
                        f"""ailed to execute function: 
                        {func.get_function_name()}, 
                        status code: {resp.status_code}, 
                        response: {resp.text}"""
                    )
                    return {
                        "error": f"""Failed to execute function:
                        {func.get_function_name()}, 
                        response: {resp.text}"""
                    }
                data = resp.json()
                if redirect_stdout:
                    print(data["stdout"])
                return json.loads(data["output"])

            func.func = wrapper
            self.tools_map[func.get_function_name()] = func
        self.entrypoint[func.get_function_name()] = entrypoint

        return self

    def reset(self) -> "DockerRuntime":
        r"""Reset the DockerRuntime instance.

        Returns:
            DockerRuntime: The DockerRuntime instance.
        """

        return self.stop().build()

    def stop(self, remove: Optional[bool] = None) -> "DockerRuntime":
        r"""stop the Docker container.

        Args:
            remove (Optional[bool]): Whether to remove the container
                after stopping it. (default::obj: `None`)

        Returns:
            DockerRuntime: The DockerRuntime instance.
        """
        if self.container:
            self.container.stop()
            if remove is None:
                remove = self.remove
            if remove:
                logger.info("Removing container.")
                self.container.remove()
            self.container = None
        else:
            logger.warning("No container to stop.")
        return self

    @property
    def ok(self) -> bool:
        r"""Check if the API Server is running.

        Returns:
            bool: Whether the API Server is running.
        """
        if not self.container:
            return False
        try:
            _ = requests.get(f"http://localhost:{self.port}")
            return True
        except requests.exceptions.ConnectionError:
            return False

    def wait(self, timeout: int = 10) -> bool:
        r"""Wait for the API Server to be ready.

        Args:
            timeout (int): The number of seconds to wait. (default::obj: `10`)

        Returns:
            bool: Whether the API Server is ready.
        """
        for _ in range(timeout):
            if self.ok:
                return True
            time.sleep(1)
        return False

    def __enter__(self) -> "DockerRuntime":
        r"""Enter the context manager.

        Returns:
            DockerRuntime: The DockerRuntime instance.
        """
        if not self.container:
            return self.build()
        logger.warning("Container already exists. Returning existing container.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        r"""Exit the context manager."""
        self.stop()

    @property
    def docs(self) -> str:
        r"""Get the URL for the API documentation.

        Returns:
            str: The URL for the API documentation.
        """
        return f"http://localhost:{self.port}/docs"
