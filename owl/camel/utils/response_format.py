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

from __future__ import annotations

import inspect
import json
from typing import Callable, Type, Union

from pydantic import BaseModel, create_model


def get_pydantic_model(
    input_data: Union[str, Type[BaseModel], Callable],
) -> Type[BaseModel]:
    r"""A multi-purpose function that can be used as a normal function,
        a class decorator, or a function decorator.

    Args:
    input_data (Union[str, type, Callable]):
        - If a string is provided, it should be a JSON-encoded string
            that will be converted into a BaseModel.
        - If a function is provided, it will be decorated such that
            its arguments are converted into a BaseModel.
        - If a BaseModel class is provided, it will be returned directly.

    Returns:
        Type[BaseModel]: The BaseModel class that will be used to
            structure the input data.
    """
    if isinstance(input_data, str):
        data_dict = json.loads(input_data)
        TemporaryModel = create_model(  # type: ignore[call-overload]
            "TemporaryModel",
            **{key: (type(value), None) for key, value in data_dict.items()},
        )
        return TemporaryModel(**data_dict).__class__

    elif callable(input_data):
        WrapperClass = create_model(  # type: ignore[call-overload]
            f"{input_data.__name__.capitalize()}Model",
            **{name: (param.annotation, ...) for name, param in inspect.signature(input_data).parameters.items()},
        )
        return WrapperClass
    if issubclass(input_data, BaseModel):
        return input_data
    raise ValueError("Invalid input data provided.")
