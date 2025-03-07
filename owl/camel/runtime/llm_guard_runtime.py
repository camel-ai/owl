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
import json
import logging
from functools import wraps
from typing import List, Optional, Union

from camel.agents import ChatAgent
from camel.configs import ChatGPTConfig
from camel.models import BaseModelBackend, ModelFactory
from camel.runtime import BaseRuntime
from camel.runtime.utils import FunctionRiskToolkit, IgnoreRiskToolkit
from camel.toolkits import FunctionTool
from camel.types import ModelPlatformType, ModelType

logger = logging.getLogger(__name__)

GUARDPROMPT = """You are a function safety evaluator tasked with assessing the 
potential risk level of a given function based on both its description 
and parameters. Your goal is to determine if the function may pose any 
harm to the user's environment, such as deleting files, executing 
arbitrary code, or accessing sensitive information. Pay special attention 
to the provided parameters — even if a function has the potential to be 
dangerous, its actual parameters may indicate harmless behavior, and the 
risk level should be adjusted accordingly. Use the `function_risk` tool to 
assign a risk score to the function, based on the following criteria:

- **Score 1**: No harm. This includes simple operations like mathematical 
    calculations, content searches, or data retrievals that do not impact 
    the user's environment or access sensitive resources. This also 
    includes functions with potentially dangerous capabilities that have 
    harmless, controlled parameters that ensure safe execution.
- **Score 2**: Minimal harm. The function might read user files, retrieve 
    non-sensitive data, or access other low-risk resources, 
    posing little risk to the user.
- **Score 3**: Risk present. The function might delete files, modify the 
    file system, execute arbitrary code, or access sensitive data, which 
    could negatively impact the user's environment. However, if the 
    actual parameters provided clearly indicate safe and restricted 
    usage, this risk should be downgraded accordingly.

When evaluating, always consider both the function's description and its 
specific parameters. If the function appears risky due to its design but 
the provided parameters indicate a safe and non-impactful operation, 
adjust the risk score to reflect this. Assign an appropriate risk score 
and provide a brief explanation of your reasoning based on the function's 
description and the actual parameters given.
YOU MUST USE THE `function_risk` TOOL TO ASSESS THE RISK 
LEVEL OF EACH FUNCTION.
"""


class LLMGuardRuntime(BaseRuntime):
    r"""A runtime that evaluates the risk level of functions using
    a language model.

    Arguments:
        prompt (str): The prompt to use for the language model. (default:
            :obj:`GUARDPROMPT`)
        model (BaseModelBackend): The language model to use. (default::obj:
            `None`)
        verbose (bool): Whether to print verbose output. (default::obj:
            `False`)
    """

    def __init__(
        self,
        prompt: str = GUARDPROMPT,
        model: Optional[BaseModelBackend] = None,
        verbose: bool = False,
    ):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.verbose = verbose

        if not self.model:
            self.model = ModelFactory.create(
                model_platform=ModelPlatformType.DEFAULT,
                model_type=ModelType.DEFAULT,
                model_config_dict=ChatGPTConfig().as_dict(),
            )
        self.ignore_toolkit = IgnoreRiskToolkit(verbose=verbose)
        self.ignore_tool = self.ignore_toolkit.get_tools()[0]
        self.tools_map[self.ignore_tool.get_function_name()] = self.ignore_tool

        self.agent = ChatAgent(
            system_message=self.prompt,
            model=self.model,
            external_tools=[
                *FunctionRiskToolkit(verbose=verbose).get_tools(),
            ],
        )

    def add(  # type: ignore[override]
        self,
        funcs: Union[FunctionTool, List[FunctionTool]],
        threshold: int = 2,
    ) -> "LLMGuardRuntime":
        r"""Add a function or list of functions to the runtime.

        Args:
            funcs (FunctionTool or List[FunctionTool]): The function or
                list of functions to add.
            threshold (int): The risk threshold for functions.
                (default::obj:`2`)

        Returns:
            LLMGuardRuntime: The current runtime.
        """

        if not isinstance(funcs, list):
            funcs = [funcs]

        for func in funcs:
            inner_func = func.func

            # Create a wrapper that explicitly binds `func`
            @wraps(inner_func)
            def wrapper(
                *args,
                func=func,
                inner_func=inner_func,
                threshold=threshold,
                **kwargs,
            ):
                function_name = func.get_function_name()
                if function_name in self.ignore_toolkit.ignored_risks:
                    reason = self.ignore_toolkit.ignored_risks.pop(function_name)
                    logger.info(f"Ignored risk for function {function_name}: {reason}")
                    return inner_func(*args, **kwargs)
                self.agent.init_messages()
                resp = self.agent.step(
                    f"""
                    Function is: {function_name}
                    Function description: {func.get_function_description()}
                    Args: {args}
                    Kwargs: {kwargs}
                    """
                )
                tool_call = resp.info.get("external_tool_request", None)
                if not tool_call:
                    logger.error("No tool call found in response.")
                    return {"error": "Risk assessment failed. Disabling function."}
                data = tool_call.function.arguments
                data = json.loads(data)
                if threshold < data["score"]:
                    message = (
                        f"Risk assessment not passed for {function_name}."
                        f"Score: {data['score']} > Threshold: {threshold}"
                        f"\nReason: {data['reason']}"
                    )
                    logger.warning(message)
                    return {"error": message}

                logger.info(
                    (
                        f"Function {function_name} passed risk assessment."
                        f"Score: {data['score']}, Reason: {data['reason']}"
                    )
                )
                if self.verbose:
                    print(
                        (
                            f"Function {function_name} passed risk assessment."
                            f"Score: {data['score']}, Reason: {data['reason']}"
                        )
                    )
                return inner_func(*args, **kwargs)

            func.func = wrapper
            self.tools_map[func.get_function_name()] = func
            self.ignore_toolkit.add(func.get_function_name())

        return self

    def reset(self) -> "LLMGuardRuntime":
        r"""Resets the runtime to its initial state."""
        self.ignore_toolkit.ignored_risks = dict()
        self.agent.reset()

        return self
