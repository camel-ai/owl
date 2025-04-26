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
import sys


from dotenv import load_dotenv
from camel.configs import ChatGPTConfig
from camel.models import ModelFactory
from camel.messages.base import BaseMessage

from camel.toolkits import (
    CodeExecutionToolkit,
    ExcelToolkit,
    FileWriteToolkit,
)
from camel.types import ModelPlatformType

from owl.utils import OwlRolePlaying
from typing import Dict, List, Optional, Tuple
from camel.logger import set_log_level, set_log_file, get_logger

import pathlib

logger = get_logger(__name__)

base_dir = pathlib.Path(__file__).parent.parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="DEBUG")

class ExcelRolePalying(OwlRolePlaying):
    def _construct_gaia_sys_msgs(self):
        user_system_prompt = f"""
### ===== 用户规则 =====  
永远不要忘记，你是用户，而我是助手。绝对不能互换角色！ 你必须始终指导我，我们的共同目标是合作完成任务。  
我的职责是帮助你完成一个复杂的任务。  

你必须根据我的专业能力和你的需求逐步指导我解决任务。  
你的指令格式必须为：  
`Instruction: [你的指令]`  
其中，"Instruction" 代表一个子任务或问题。  

- 你每次只能给出一个指令。  
- 我必须依据你的指令提供适当的解决方案。  
- 你只能指导我，而不能向我提问。  

---

### 请注意  
任务可能会非常复杂，不要试图一次性解决整个任务！  
你必须让我一步一步地寻找答案。  

以下是一些能帮助你给出更有价值指令的提示：  

#### <tips>
- 我可以使用各种工具，比如：excel Toolkit 和 code Execution Toolkit 等。

- 尽管任务复杂，但答案是存在的。  
  如果你发现当前方案无法找到答案，请重新规划任务，使用其他方法或工具来达到相同的目标。  

- 务必提醒我验证最终答案是否正确！  
  这可以通过多种方式完成，例如截图、网页分析等。  

- 如果我编写了代码，请提醒我运行代码并获取结果。  

- 请灵活使用代码解决问题，尤其是涉及 Excel 相关任务时。  

</tips>

---

### 任务描述  
当前任务如下：  
<task>{self.task_prompt}</task>  
永远不要忘记这个任务！  

### 任务执行规则  
你现在必须开始 逐步指导我完成任务。  
- 不要添加任何额外的内容！  
- 继续给出指令，直到你认为任务完成。  

### 任务完成规则  
当任务完成时，你只能回复一个单词：  
`<TASK_DONE>`  

在我的回答完全解决你的任务之前，绝对不要说 `<TASK_DONE>`！
        """

        assistant_system_prompt = f"""
===== 助手规则 =====  
永远不要忘记，你是助手，而我是用户。绝对不能互换角色！ 绝对不能指挥我！ 你必须利用你的工具来解决我分配的任务。  
我们的共同目标是合作完成一个复杂的任务。  
你的职责是帮助我完成任务。  

当前任务如下：  
{self.task_prompt}  
永远不要忘记这个任务！  

我会根据你的专业能力和我的需求指导你完成任务。  
每条指令通常是一个子任务或问题。  

你必须充分利用你的工具，尽力解决问题，并详细解释你的解决方案。  
除非我宣布任务完成，你的回答必须以以下格式开始：  

Solution: [你的解决方案]  

[你的解决方案] 必须具体，包含详细的解释，并提供可行的实现方案、示例或清单来解决任务。  

---

### 请注意：整体任务可能会非常复杂！  
以下是一些可能帮助你解决任务的重要提示：  

#### <tips>  
- 如果一种方法失败了，尝试其他方法。答案是存在的！  
- 当涉及到查看某个excel信息的时候，你可以总是以编写python代码读入excel文件查看sheet名，列名之类的信息开始。
- 当你尝试给出python代码的时候，始终记得在最开头import相关的库，比如下面这些excel分析常见的库
```
import pandas as pd
```
- 始终验证你的最终答案是否正确！  
- 请每次都从头开始编写完整代码，编写代码后，务必运行代码并获取结果！  
  如果遇到错误，尝试调试代码。  
- 如果工具运行失败，或者代码无法正确运行，  
  绝对不要假设其返回了正确结果，并在此基础上继续推理！  
  正确的做法是分析错误原因，并尝试修正！  
- [重要！！！]如果你写的代码涉及到用matplotlib画图，请始终在代码开头下面这段代码：
```
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 支持中文
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
```
- 请始终使用英文来画图，比如title, xlabel, ylabel以及其他均使用英文。
</tips>
        """

        user_sys_msg = BaseMessage.make_user_message(
            role_name=self.user_role_name, content=user_system_prompt
        )

        assistant_sys_msg = BaseMessage.make_assistant_message(
            role_name=self.assistant_role_name, content=assistant_system_prompt
        )

        return user_sys_msg, assistant_sys_msg

def run_society(
    society: OwlRolePlaying,
    round_limit: int = 15,
) -> Tuple[str, List[dict], dict]:
    overall_completion_token_count = 0
    overall_prompt_token_count = 0

    chat_history = []
    init_prompt = """
现在请给我逐步解决整个任务的指令。如果任务需要一些特定的知识，请指示我使用工具来完成任务。
        """
    input_msg = society.init_chat(init_prompt)
    for _round in range(round_limit):
        assistant_response, user_response = society.step(input_msg)
        # Check if usage info is available before accessing it
        if assistant_response.info.get("usage") and user_response.info.get("usage"):
            overall_completion_token_count += assistant_response.info["usage"].get(
                "completion_tokens", 0
            ) + user_response.info["usage"].get("completion_tokens", 0)
            overall_prompt_token_count += assistant_response.info["usage"].get(
                "prompt_tokens", 0
            ) + user_response.info["usage"].get("prompt_tokens", 0)

        # convert tool call to dict
        tool_call_records: List[dict] = []
        if assistant_response.info.get("tool_calls"):
            for tool_call in assistant_response.info["tool_calls"]:
                tool_call_records.append(tool_call.as_dict())

        _data = {
            "user": user_response.msg.content
            if hasattr(user_response, "msg") and user_response.msg
            else "",
            "assistant": assistant_response.msg.content
            if hasattr(assistant_response, "msg") and assistant_response.msg
            else "",
            "tool_calls": tool_call_records,
        }

        chat_history.append(_data)
        logger.info(
            f"Round #{_round} user_response:\n {user_response.msgs[0].content if user_response.msgs and len(user_response.msgs) > 0 else ''}"
        )
        logger.info(
            f"Round #{_round} assistant_response:\n {assistant_response.msgs[0].content if assistant_response.msgs and len(assistant_response.msgs) > 0 else ''}"
        )

        if (
            assistant_response.terminated
            or user_response.terminated
            or "TASK_DONE" in user_response.msg.content
        ):
            break

        input_msg = assistant_response.msg

    answer = chat_history[-1]["assistant"]
    token_info = {
        "completion_token_count": overall_completion_token_count,
        "prompt_token_count": overall_prompt_token_count,
    }

    return answer, chat_history, token_info

def construct_society(question: str) -> ExcelRolePalying:
    r"""Construct a society of agents based on the given question.

    Args:
        question (str): The task or question to be addressed by the society.

    Returns:
        OwlRolePlaying: A configured society of agents ready to address the question.
    """

    base_model_config = {
        "model_platform": ModelPlatformType.DEEPSEEK,
        "model_type": 'deepseek-chat',
        "model_config_dict": ChatGPTConfig(temperature=0.1, max_tokens=8192).as_dict(),
    }

    # Create models for different components using Azure OpenAI
    # base_model_config = {
    #     "model_platform": ModelPlatformType.AZURE,
    #     "model_type": os.getenv("AZURE_OPENAI_MODEL_TYPE"),
    #     "model_config_dict": ChatGPTConfig(temperature=0.4, max_tokens=4096).as_dict(),
    # }


    models = {
        "user": ModelFactory.create(**base_model_config),
        "assistant": ModelFactory.create(**base_model_config),
    }

    # Configure toolkits
    tools = [
        *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
        *ExcelToolkit().get_tools(),
        *FileWriteToolkit(output_dir="./").get_tools(),
    ]

    # Configure agent roles and parameters
    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}

    # Configure task parameters
    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    # Create and return the society
    society = ExcelRolePalying(
        **task_kwargs,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
        output_language="中文"
    )

    return society


def main():
    r"""Main function to run the OWL system with Azure OpenAI."""
    # Example question
    # default_task = """帮忙分析一下这个文件中各个学院的录取人数以及最高分最低分，把这些信息画到一张图上，并存到当前路径下。文件路径是`./data/admission_zh.xlsx`"""

    default_task = """帮忙分析一下`./data/admission_zh.xlsx`这个文件，请你：
    - 统计各个学院的录取人数以及最高分最低分
    - 把这些信息画到一张图上，录取人数使用柱状图，最高分最低分使用折线图
    - 把画完的图`vis_zh.png`存到当前目录下"""


    set_log_file('log.txt')

    # Override default task if command line argument is provided
    task = sys.argv[1] if len(sys.argv) > 1 else default_task

    # Construct and run the society
    society = construct_society(task)

    answer, chat_history, token_count = run_society(society)

    # Output the result
    print(f"\033[94mAnswer: {answer}\033[0m")


if __name__ == "__main__":
    main()
