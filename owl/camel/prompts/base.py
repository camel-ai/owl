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
import inspect
from typing import Any, Callable, Dict, Optional, Set, TypeVar, Union

from camel.interpreters import BaseInterpreter, SubprocessInterpreter
from camel.types import RoleType
from camel.utils import get_system_information

T = TypeVar("T")


def return_prompt_wrapper(
    cls: Any,
    func: Callable,
) -> Callable[..., Union[Any, tuple]]:
    r"""Wrapper that converts the return value of a function to an input
    class instance if it's a string.

    Args:
        cls (Any): The class to convert to.
        func (Callable): The function to decorate.

    Returns:
        Callable[..., Union[Any, str]]: Decorated function that
            returns the decorated class instance if the return value is a
            string.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Union[Any, str]:
        r"""Wrapper function that performs the conversion to :obj:`TextPrompt`
            instance.

        Args:
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Union[Any, str]: The converted return value.
        """
        result = func(*args, **kwargs)
        if isinstance(result, str) and not isinstance(result, cls):
            return cls(result)
        elif isinstance(result, tuple):
            new_result = tuple(
                cls(item) if isinstance(item, str) and not isinstance(item, cls) else item for item in result
            )
            return new_result
        return result

    # # Preserve the original function's attributes
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__

    return wrapper


def wrap_prompt_functions(cls: T) -> T:
    r"""Decorator that wraps functions of a class inherited from :obj:`str`
    with the :obj:`return_text_prompt` decorator.

    Args:
        cls (type): The class to decorate.

    Returns:
        type: Decorated class with wrapped functions.
    """
    excluded_attrs = {"__init__", "__new__", "__str__", "__repr__"}
    for attr_name in dir(cls):
        attr_value = getattr(cls, attr_name)
        if callable(attr_value) and attr_name not in excluded_attrs:
            if inspect.isroutine(attr_value):
                setattr(cls, attr_name, return_prompt_wrapper(cls, attr_value))
    return cls


@wrap_prompt_functions
class TextPrompt(str):
    r"""A class that represents a text prompt. The :obj:`TextPrompt` class
    extends the built-in :obj:`str` class to provide a property for retrieving
    the set of keywords in the prompt.

    Attributes:
        key_words (set): A set of strings representing the keywords in the
            prompt.
    """

    @property
    def key_words(self) -> Set[str]:
        r"""Returns a set of strings representing the keywords in the prompt."""
        from camel.utils import get_prompt_template_key_words

        return get_prompt_template_key_words(self)

    def format(self, *args: Any, **kwargs: Any) -> "TextPrompt":
        r"""Overrides the built-in :obj:`str.format` method to allow for
        default values in the format string. This is used to allow formatting
        the partial string.

        Args:
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            TextPrompt: A new :obj:`TextPrompt` object with the format string
                replaced with the formatted string.
        """
        default_kwargs = {key: "{" + f"{key}" + "}" for key in self.key_words}
        default_kwargs.update(kwargs)
        return TextPrompt(super().format(*args, **default_kwargs))


@wrap_prompt_functions
class CodePrompt(TextPrompt):
    r"""A class that represents a code prompt. It extends the :obj:`TextPrompt`
    class with a :obj:`code_type` property.

    Attributes:
        code_type (str, optional): The type of code. Defaults to None.
    """

    def __new__(cls, *args: Any, **kwargs: Any) -> "CodePrompt":
        r"""Creates a new instance of the :obj:`CodePrompt` class.

        Args:
            *args (Any): Positional arguments.
            **kwargs (Any): Keyword arguments.

        Returns:
            CodePrompt: The created :obj:`CodePrompt` instance.
        """
        code_type = kwargs.pop("code_type", None)
        instance = super().__new__(cls, *args, **kwargs)
        instance._code_type = code_type
        return instance

    @property
    def code_type(self) -> Optional[str]:
        r"""Returns the type of code.

        Returns:
            Optional[str]: The type of code.
        """
        return self._code_type

    def set_code_type(self, code_type: str) -> None:
        r"""Sets the type of code.

        Args:
            code_type (str): The type of code.
        """
        self._code_type = code_type

    def execute(
        self,
        interpreter: Optional[BaseInterpreter] = None,
        **kwargs: Any,
    ) -> str:
        r"""Executes the code string using the provided interpreter.

        This method runs a code string through either a specified interpreter
        or a default one. It supports additional keyword arguments for
        flexibility.

        Args:
            interpreter (Optional[BaseInterpreter]): The interpreter instance
                to use for execution. If `None`, a default interpreter is used.
                (default: :obj:`None`)
            **kwargs: Additional keyword arguments passed to the interpreter to
                run the code.

        Returns:
            str: The result of the code execution. If the execution fails, this
                should include sufficient information to diagnose and correct
                the issue.

        Raises:
            InterpreterError: If the code execution encounters errors that
                could be resolved by modifying or regenerating the code.
        """
        if interpreter is None:
            execution_res = SubprocessInterpreter().run(self, self._code_type, **kwargs)
        else:
            execution_res = interpreter.run(self, self._code_type, **kwargs)
        return execution_res


# flake8: noqa :E501
class TextPromptDict(Dict[Any, TextPrompt]):
    r"""A dictionary class that maps from key to :obj:`TextPrompt` object."""

    EMBODIMENT_PROMPT = TextPrompt(
        "System information :"
        + "\n".join(f"{key}: {value}" for key, value in get_system_information().items())
        + "\n"
        + """You are the physical embodiment of the {role} who is working on solving a task: {task}.
You can do things in the physical world including browsing the Internet, reading documents, drawing images, creating videos, executing code and so on.
Your job is to perform the physical actions necessary to interact with the physical world.
You will receive thoughts from the {role} and you will need to perform the actions described in the thoughts.
You can write a series of simple commands in to act.
You can perform a set of actions by calling the available functions.
You should perform actions based on the descriptions of the functions.

Here is your action space but it is not limited:
{action_space}

You can perform multiple actions.
You can perform actions in any order.
First, explain the actions you will perform and your reasons, then write code to implement your actions.
If you decide to perform actions, you must write code to implement the actions.
You may print intermediate results if necessary."""
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update({RoleType.EMBODIMENT: self.EMBODIMENT_PROMPT})
