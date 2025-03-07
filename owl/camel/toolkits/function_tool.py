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
import ast
import inspect
import logging
import warnings
from inspect import Parameter, getsource, signature
from typing import Any, Callable, Dict, Mapping, Optional, Tuple, Type

from docstring_parser import parse
from jsonschema.exceptions import SchemaError
from jsonschema.validators import Draft202012Validator as JSONValidator
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from camel.agents import ChatAgent
from camel.models import BaseModelBackend, ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.utils import get_pydantic_object_schema, to_pascal

logger = logging.getLogger(__name__)


def _remove_a_key(d: Dict, remove_key: Any) -> None:
    r"""Remove a key from a dictionary recursively."""
    if isinstance(d, dict):
        for key in list(d.keys()):
            if key == remove_key:
                del d[key]
            else:
                _remove_a_key(d[key], remove_key)


def _remove_title_recursively(data, parent_key=None):
    r"""Recursively removes the 'title' key from all levels of a nested
    dictionary, except when 'title' is an argument name in the schema.
    """
    if isinstance(data, dict):
        # Only remove 'title' if it's not an argument name
        if parent_key not in [
            "properties",
            "$defs",
            "items",
            "allOf",
            "oneOf",
            "anyOf",
        ]:
            data.pop("title", None)

        # Recursively process each key-value pair
        for key, value in data.items():
            _remove_title_recursively(value, parent_key=key)
    elif isinstance(data, list):
        # Recursively process each element in the list
        for item in data:
            _remove_title_recursively(item, parent_key=parent_key)


def get_openai_function_schema(func: Callable) -> Dict[str, Any]:
    r"""Generates a schema dict for an OpenAI function based on its signature.

    This function is deprecated and will be replaced by
    :obj:`get_openai_tool_schema()` in future versions. It parses the
    function's parameters and docstring to construct a JSON schema-like
    dictionary.

    Args:
        func (Callable): The OpenAI function to generate the schema for.

    Returns:
        Dict[str, Any]: A dictionary representing the JSON schema of the
            function, including its name, description, and parameter
            specifications.
    """
    openai_function_schema = get_openai_tool_schema(func)["function"]
    return openai_function_schema


def get_openai_tool_schema(func: Callable) -> Dict[str, Any]:
    r"""Generates an OpenAI JSON schema from a given Python function.

    This function creates a schema compatible with OpenAI's API specifications,
    based on the provided Python function. It processes the function's
    parameters, types, and docstrings, and constructs a schema accordingly.

    Note:
        - Each parameter in `func` must have a type annotation; otherwise, it's
          treated as 'Any'.
        - Variable arguments (*args) and keyword arguments (**kwargs) are not
          supported and will be ignored.
        - A functional description including a brief and detailed explanation
          should be provided in the docstring of `func`.
        - All parameters of `func` must be described in its docstring.
        - Supported docstring styles: ReST, Google, Numpydoc, and Epydoc.

    Args:
        func (Callable): The Python function to be converted into an OpenAI
                         JSON schema.

    Returns:
        Dict[str, Any]: A dictionary representing the OpenAI JSON schema of
                        the provided function.

    See Also:
        `OpenAI API Reference
            <https://platform.openai.com/docs/api-reference/assistants/object>`_
    """
    params: Mapping[str, Parameter] = signature(func).parameters
    fields: Dict[str, Tuple[type, FieldInfo]] = {}
    for param_name, p in params.items():
        param_type = p.annotation
        param_default = p.default
        param_kind = p.kind
        param_annotation = p.annotation
        # Variable parameters are not supported
        if param_kind == Parameter.VAR_POSITIONAL or param_kind == Parameter.VAR_KEYWORD:
            continue
        # If the parameter type is not specified, it defaults to typing.Any
        if param_annotation is Parameter.empty:
            param_type = Any
        # Check if the parameter has a default value
        if param_default is Parameter.empty:
            fields[param_name] = (param_type, FieldInfo())
        else:
            fields[param_name] = (param_type, FieldInfo(default=param_default))

    # Applying `create_model()` directly will result in a mypy error,
    # create an alias to avoid this.
    def _create_mol(name, field):
        return create_model(name, **field)

    model = _create_mol(to_pascal(func.__name__), fields)
    parameters_dict = get_pydantic_object_schema(model)

    # The `"title"` is generated by `model.model_json_schema()`
    # but is useless for openai json schema, remove generated 'title' from
    # parameters_dict
    _remove_title_recursively(parameters_dict)

    docstring = parse(func.__doc__ or "")
    for param in docstring.params:
        if (name := param.arg_name) in parameters_dict["properties"] and (description := param.description):
            parameters_dict["properties"][name]["description"] = description

    short_description = docstring.short_description or ""
    long_description = docstring.long_description or ""
    if long_description:
        func_description = f"{short_description}\n{long_description}"
    else:
        func_description = short_description

    openai_function_schema = {
        "name": func.__name__,
        "description": func_description,
        "parameters": parameters_dict,
    }

    openai_tool_schema = {
        "type": "function",
        "function": openai_function_schema,
    }
    return openai_tool_schema


def generate_docstring(
    code: str,
    model: Optional[BaseModelBackend] = None,
) -> str:
    r"""Generates a docstring for a given function code using LLM.

    This function leverages a language model to generate a
    PEP 8/PEP 257-compliant docstring for a provided Python function.
    If no model is supplied, a default gpt-4o-mini is used.

    Args:
        code (str): The source code of the function.
        model (Optional[BaseModelBackend]): An optional language model backend
            instance. If not provided, a default gpt-4o-mini is used.

    Returns:
        str: The generated docstring.
    """
    # Create the docstring prompt
    docstring_prompt = """
    **Role**: Generate professional Python docstrings conforming to 
    PEP 8/PEP 257.

    **Requirements**:
    - Use appropriate format: reST, Google, or NumPy, as needed.
    - Include parameters, return values, and exceptions.
    - Reference any existing docstring in the function and 
      retain useful information.

    **Input**: Python function.

    **Output**: Docstring content (plain text, no code markers).

    **Example:**

    Input:
    ```python
    def add(a: int, b: int) -> int:
        return a + b
    ```

    Output:
    Adds two numbers.
    Args:
        a (int): The first number.
        b (int): The second number.

    Returns:
        int: The sum of the two numbers.

    **Task**: Generate a docstring for the function below.

    """
    # Initialize assistant with system message and model
    assistant_sys_msg = "You are a helpful assistant."
    docstring_assistant = ChatAgent(assistant_sys_msg, model=model)

    # Create user message to prompt the assistant
    user_msg = docstring_prompt + code

    # Get the response containing the generated docstring
    response = docstring_assistant.step(user_msg)
    return response.msg.content


class FunctionTool:
    r"""An abstraction of a function that OpenAI chat models can call. See
    https://platform.openai.com/docs/api-reference/chat/create.

    By default, the tool schema will be parsed from the func, or you can
    provide a user-defined tool schema to override.

    Args:
        func (Callable): The function to call. The tool schema is parsed from
            the function signature and docstring by default.
        openai_tool_schema (Optional[Dict[str, Any]], optional): A
            user-defined OpenAI tool schema to override the default result.
            (default: :obj:`None`)
        synthesize_schema (Optional[bool], optional): Whether to enable the
            use of a schema assistant model to automatically synthesize the
            schema if validation fails or no valid schema is provided.
            (default: :obj:`False`)
        synthesize_schema_model (Optional[BaseModelBackend], optional): An
            assistant model (e.g., an LLM model) used to synthesize the schema
            if `synthesize_schema` is enabled and no valid schema is
            provided. (default: :obj:`None`)
        synthesize_schema_max_retries (int, optional): The maximum
            number of attempts to retry schema synthesis using the schema
            assistant model if the previous attempts fail. (default: 2)
        synthesize_output (Optional[bool], optional): Flag for enabling
            synthesis output mode, where output is synthesized based on the
            function's execution. (default: :obj:`False`)
        synthesize_output_model (Optional[BaseModelBackend], optional):
            Model used for output synthesis in synthesis mode.
            (default: :obj:`None`)
        synthesize_output_format (Optional[Type[BaseModel]], optional): Format
            for the response when synthesizing output. (default: :obj:`None`)
    """

    def __init__(
        self,
        func: Callable,
        openai_tool_schema: Optional[Dict[str, Any]] = None,
        synthesize_schema: Optional[bool] = False,
        synthesize_schema_model: Optional[BaseModelBackend] = None,
        synthesize_schema_max_retries: int = 2,
        synthesize_output: Optional[bool] = False,
        synthesize_output_model: Optional[BaseModelBackend] = None,
        synthesize_output_format: Optional[Type[BaseModel]] = None,
    ) -> None:
        self.func = func
        self.openai_tool_schema = openai_tool_schema or get_openai_tool_schema(func)
        self.synthesize_output = synthesize_output
        self.synthesize_output_model = synthesize_output_model
        if synthesize_output and synthesize_output_model is None:
            self.synthesize_output_model = ModelFactory.create(
                model_platform=ModelPlatformType.DEFAULT,
                model_type=ModelType.DEFAULT,
            )
            logger.warning(
                "Warning: No synthesize_output_model provided. "
                f"Use `{self.synthesize_output_model.model_type}` to "
                "synthesize the output."
            )
        self.synthesize_output_format: Optional[type[BaseModel]] = None
        return_annotation = inspect.signature(self.func).return_annotation
        if synthesize_output_format is not None:
            self.synthesize_output_format = synthesize_output_format
        elif isinstance(return_annotation, type) and issubclass(return_annotation, BaseModel):
            self.synthesize_output_format = return_annotation

        self.synthesize_schema_model = synthesize_schema_model
        if synthesize_schema:
            if openai_tool_schema:
                logger.warning(
                    """The user-defined OpenAI tool schema will be
                              overridden by the schema assistant model."""
                )
            if self.synthesize_schema_model is None:
                self.synthesize_schema_model = ModelFactory.create(
                    model_platform=ModelPlatformType.DEFAULT,
                    model_type=ModelType.DEFAULT,
                )
                logger.warning(
                    "Warning: No synthesize_schema_model provided. "
                    f"Use `{self.synthesize_schema_model.model_type}` to "
                    "synthesize the schema."
                )
            schema = self.synthesize_openai_tool_schema(synthesize_schema_max_retries)
            if schema:
                self.openai_tool_schema = schema
            else:
                raise ValueError(f"Failed to synthesize a valid schema for " f"{self.func.__name__}.")

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self.synthesize_output:
            result = self.synthesize_execution_output(args, kwargs)
            return result
        else:
            # Pass the extracted arguments to the indicated function
            try:
                result = self.func(*args, **kwargs)
                return result
            except Exception as e:
                raise ValueError(
                    f"Execution of function {self.func.__name__} failed with "
                    f"arguments {args} and {kwargs}. "
                    f"Error: {e}"
                )

    @staticmethod
    def validate_openai_tool_schema(
        openai_tool_schema: Dict[str, Any],
    ) -> None:
        r"""Validates the OpenAI tool schema against
        :obj:`ToolAssistantToolsFunction`.
        This function checks if the provided :obj:`openai_tool_schema` adheres
        to the specifications required by OpenAI's
        :obj:`ToolAssistantToolsFunction`. It ensures that the function
        description and parameters are correctly formatted according to JSON
        Schema specifications.
        Args:
            openai_tool_schema (Dict[str, Any]): The OpenAI tool schema to
                validate.
        Raises:
            ValidationError: If the schema does not comply with the
                specifications.
            SchemaError: If the parameters do not meet JSON Schema reference
                specifications.
        """
        # Check the type
        if not openai_tool_schema["type"]:
            raise ValueError("miss `type` in tool schema.")

        # Check the function description, if no description then raise warming
        if not openai_tool_schema["function"].get("description"):
            warnings.warn(
                f"""Function description is missing for 
                          {openai_tool_schema['function']['name']}. This may 
                          affect the quality of tool calling."""
            )

        # Validate whether parameters
        # meet the JSON Schema reference specifications.
        # See https://platform.openai.com/docs/guides/gpt/function-calling
        # for examples, and the
        # https://json-schema.org/understanding-json-schema/ for
        # documentation about the format.
        parameters = openai_tool_schema["function"]["parameters"]
        try:
            JSONValidator.check_schema(parameters)
        except SchemaError as e:
            raise e

        # Check the parameter description, if no description then raise warming
        properties: Dict[str, Any] = parameters["properties"]
        for param_name in properties.keys():
            param_dict = properties[param_name]
            if "description" not in param_dict:
                warnings.warn(
                    f"""Parameter description is missing for 
                            {param_dict}. This may affect the quality of tool 
                            calling."""
                )

    def get_openai_tool_schema(self) -> Dict[str, Any]:
        r"""Gets the OpenAI tool schema for this function.

        This method returns the OpenAI tool schema associated with this
        function, after validating it to ensure it meets OpenAI's
        specifications.

        Returns:
            Dict[str, Any]: The OpenAI tool schema for this function.
        """
        self.validate_openai_tool_schema(self.openai_tool_schema)
        return self.openai_tool_schema

    def set_openai_tool_schema(self, schema: Dict[str, Any]) -> None:
        r"""Sets the OpenAI tool schema for this function.

        Allows setting a custom OpenAI tool schema for this function.

        Args:
            schema (Dict[str, Any]): The OpenAI tool schema to set.
        """
        self.openai_tool_schema = schema

    def get_openai_function_schema(self) -> Dict[str, Any]:
        r"""Gets the schema of the function from the OpenAI tool schema.

        This method extracts and returns the function-specific part of the
        OpenAI tool schema associated with this function.

        Returns:
            Dict[str, Any]: The schema of the function within the OpenAI tool
                schema.
        """
        self.validate_openai_tool_schema(self.openai_tool_schema)
        return self.openai_tool_schema["function"]

    def set_openai_function_schema(
        self,
        openai_function_schema: Dict[str, Any],
    ) -> None:
        r"""Sets the schema of the function within the OpenAI tool schema.

        Args:
            openai_function_schema (Dict[str, Any]): The function schema to
                set within the OpenAI tool schema.
        """
        self.openai_tool_schema["function"] = openai_function_schema

    def get_function_name(self) -> str:
        r"""Gets the name of the function from the OpenAI tool schema.

        Returns:
            str: The name of the function.
        """
        self.validate_openai_tool_schema(self.openai_tool_schema)
        return self.openai_tool_schema["function"]["name"]

    def set_function_name(self, name: str) -> None:
        r"""Sets the name of the function in the OpenAI tool schema.

        Args:
            name (str): The name of the function to set.
        """
        self.openai_tool_schema["function"]["name"] = name

    def get_function_description(self) -> str:
        r"""Gets the description of the function from the OpenAI tool
        schema.

        Returns:
            str: The description of the function.
        """
        self.validate_openai_tool_schema(self.openai_tool_schema)
        return self.openai_tool_schema["function"]["description"]

    def set_function_description(self, description: str) -> None:
        r"""Sets the description of the function in the OpenAI tool schema.

        Args:
            description (str): The description for the function.
        """
        self.openai_tool_schema["function"]["description"] = description

    def get_paramter_description(self, param_name: str) -> str:
        r"""Gets the description of a specific parameter from the function
        schema.

        Args:
            param_name (str): The name of the parameter to get the
                description.

        Returns:
            str: The description of the specified parameter.
        """
        self.validate_openai_tool_schema(self.openai_tool_schema)
        return self.openai_tool_schema["function"]["parameters"]["properties"][param_name]["description"]

    def set_paramter_description(
        self,
        param_name: str,
        description: str,
    ) -> None:
        r"""Sets the description for a specific parameter in the function
        schema.

        Args:
            param_name (str): The name of the parameter to set the description
                for.
            description (str): The description for the parameter.
        """
        self.openai_tool_schema["function"]["parameters"]["properties"][param_name]["description"] = description

    def get_parameter(self, param_name: str) -> Dict[str, Any]:
        r"""Gets the schema for a specific parameter from the function schema.

        Args:
            param_name (str): The name of the parameter to get the schema.

        Returns:
            Dict[str, Any]: The schema of the specified parameter.
        """
        self.validate_openai_tool_schema(self.openai_tool_schema)
        return self.openai_tool_schema["function"]["parameters"]["properties"][param_name]

    def set_parameter(self, param_name: str, value: Dict[str, Any]):
        r"""Sets the schema for a specific parameter in the function schema.

        Args:
            param_name (str): The name of the parameter to set the schema for.
            value (Dict[str, Any]): The schema to set for the parameter.
        """
        try:
            JSONValidator.check_schema(value)
        except SchemaError as e:
            raise e
        self.openai_tool_schema["function"]["parameters"]["properties"][param_name] = value

    def synthesize_openai_tool_schema(
        self,
        max_retries: Optional[int] = None,
    ) -> Dict[str, Any]:
        r"""Synthesizes an OpenAI tool schema for the specified function.

        This method uses a language model (LLM) to synthesize the OpenAI tool
        schema for the specified function by first generating a docstring and
        then creating a schema based on the function's source code. The
        schema synthesis and validation process is retried up to
        `max_retries` times in case of failure.

        Args:
            max_retries (Optional[int], optional): The maximum number of
                retries for schema synthesis and validation if the process
                fails. (default: :obj:`None`)

        Returns:
            Dict[str, Any]: The synthesis OpenAI tool schema for the function.

        Raises:
            ValueError: If schema synthesis or validation fails after the
                maximum number of retries, a ValueError is raised, prompting
                manual schema setting.
        """
        code = getsource(self.func)
        retries = 0
        if max_retries is None:
            max_retries = 0
        # Retry loop to handle schema synthesis and validation
        while retries <= max_retries:
            try:
                # Generate the docstring and the schema
                docstring = generate_docstring(code, self.synthesize_schema_model)
                self.func.__doc__ = docstring
                schema = get_openai_tool_schema(self.func)
                # Validate the schema
                self.validate_openai_tool_schema(schema)
                return schema

            except Exception as e:
                retries += 1
                if retries == max_retries:
                    raise ValueError(
                        f"Failed to synthesize the OpenAI tool Schema after "
                        f"{max_retries} retries. "
                        f"Please set the OpenAI tool schema for "
                        f"function {self.func.__name__} manually."
                    ) from e
                logger.warning("Schema validation failed. Retrying...")

        return {}

    def synthesize_execution_output(
        self,
        args: Optional[tuple[Any, ...]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        r"""Synthesizes the output of the function based on the provided
        positional arguments and keyword arguments.

        Args:
            args (Optional[tuple]): Positional arguments to pass to the
                function during synthesis. (default: :obj:`None`)
            kwargs (Optional[Dict[str, Any]]): Keyword arguments to pass to the
                function during synthesis. (default: :obj:`None`)

        Returns:
            Any: Synthesized output from the function execution. If no
                synthesis model is provided, a warning is logged.
        """
        import textwrap

        # Retrieve the function source code
        function_string = inspect.getsource(self.func)

        # Check and update docstring if necessary
        if self.func.__doc__ is not None:
            function_string = textwrap.dedent(function_string)
            tree = ast.parse(function_string)
            func_node = tree.body[0] if isinstance(tree.body[0], ast.FunctionDef) else None
            if func_node:
                existing_docstring = ast.get_docstring(func_node)
                if existing_docstring != self.func.__doc__:
                    func_node.body[0] = ast.Expr(value=ast.Constant(value=self.func.__doc__, kind=None))
                    function_string = ast.unparse(tree)

        # Append the args and kwargs information to the function string
        if args:
            function_string += f"\nargs:\n{list(args)}"
        if kwargs:
            function_string += f"\nkwargs:\n{kwargs}"

        # Define the assistant system message
        assistant_sys_msg = '''
**Role:** AI Assistant specialized in synthesizing tool execution outputs
without actual execution.

**Capabilities:**
- Analyzes function to understand their
  purpose and expected outputs.
- Generates synthetic outputs based on the function logic.
- Ensures the synthesized output is contextually accurate and aligns with the
  function's intended behavior.

**Instructions:**
1. **Input:** Provide the function code, function docstring, args, and kwargs.
2. **Output:** Synthesize the expected output of the function based on the
   provided args and kwargs.

**Example:**
- **User Input:**
def sum(a, b, c=0):
    """Adds three numbers together."""
    return a + b + c

- **Input Arguments:**
args: (1, 2)
kwargs: {"c": 3}

- **Output:**
6

**Note:**
- Just return the synthesized output of the function without any explanation.
- The output should be in plain text without any formatting.
'''

        # Initialize the synthesis agent
        synthesis_agent = ChatAgent(
            assistant_sys_msg,
            model=self.synthesize_output_model,
        )

        # User message combining function string and additional context
        user_msg = function_string
        response = synthesis_agent.step(
            user_msg,
            response_format=self.synthesize_output_format,
        )

        return response.msg.content

    @property
    def parameters(self) -> Dict[str, Any]:
        r"""Getter method for the property :obj:`parameters`.

        Returns:
            Dict[str, Any]: the dictionary containing information of
                parameters of this function.
        """
        self.validate_openai_tool_schema(self.openai_tool_schema)
        return self.openai_tool_schema["function"]["parameters"]["properties"]

    @parameters.setter
    def parameters(self, value: Dict[str, Any]) -> None:
        r"""Setter method for the property :obj:`parameters`. It will
        firstly check if the input parameters schema is valid. If invalid,
        the method will raise :obj:`jsonschema.exceptions.SchemaError`.

        Args:
            value (Dict[str, Any]): the new dictionary value for the
                function's parameters.
        """
        try:
            JSONValidator.check_schema(value)
        except SchemaError as e:
            raise e
        self.openai_tool_schema["function"]["parameters"]["properties"] = value
