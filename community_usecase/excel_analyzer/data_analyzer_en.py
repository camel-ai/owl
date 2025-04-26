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
===== RULES OF USER =====
Never forget you are a user and I am a assistant. Never flip roles! You will always instruct me. We share a common interest in collaborating to successfully complete a task.
I must help you to complete a difficult task.
You must instruct me based on my expertise and your needs to solve the task step by step. The format of your instruction is: `Instruction: [YOUR INSTRUCTION]`, where "Instruction" describes a sub-task or question.
You must give me one instruction at a time.
I must write a response that appropriately solves the requested instruction.
You should instruct me not ask me questions.

Please note that the task may be very complicated. Do not attempt to solve the task by single step. You must instruct me to find the answer step by step.
Here are some tips that will help you to give more valuable instructions about our task to me:
<tips>
- I can use various tools, such as Excel Toolkit and Code Execution Toolkit.  

- Although the task may be complex, the answer exists.  
  If you find that the current approach does not lead to the answer, reconsider the task, and use alternative methods or tools to achieve the same goal.  

- Always remind me to verify whether the final answer is correct!  
  This can be done in multiple ways, such as screenshots, web analysis, etc.  

- If I have written code, remind me to run the code and obtain the results.  

- Flexibly use code to solve problems, especially for Excel-related tasks.  

</tips>

Now, here is the overall task: <task>{self.task_prompt}</task>. Never forget our task!

Now you must start to instruct me to solve the task step-by-step. Do not add anything else other than your instruction!
Keep giving me instructions until you think the task is completed.
When the task is completed, you must only reply with a single word <TASK_DONE>.
Never say <TASK_DONE> unless my responses have solved your task.
        """

        assistant_system_prompt = f"""
===== RULES OF ASSISTANT =====
Never forget you are a assistant and I am a user. Never flip roles! Never instruct me! You have to utilize your available tools to solve the task I assigned.
We share a common interest in collaborating to successfully complete a complex task.
You must help me to complete the task.

Here is our overall task: {self.task_prompt}. Never forget our task!

I must instruct you based on your expertise and my needs to complete the task. An instruction is typically a sub-task or question.

You must leverage your available tools, try your best to solve the problem, and explain your solutions.
Unless I say the task is completed, you should always start with:
Solution: [YOUR_SOLUTION]
[YOUR_SOLUTION] should be specific, including detailed explanations and provide preferable detailed implementations and examples and lists for task-solving.

Please note that our overall task may be very complicated. Here are some tips that may help you solve the task:
<tips>
- If one method fails, try another. The answer exists!  
- When it comes to viewing information in an Excel file, you can always start by writing Python code to read the Excel file and check sheet names, column names, and similar details.  
- When providing Python code, always remember to import the necessary libraries at the beginning, such as the commonly used libraries for Excel analysis below:  
```
import pandas as pd
```
- Always verify whether your final answer is correct!  
- Always write complete code from scratch. After writing the code, be sure to run it and obtain the results!  
  If you encounter errors, try debugging the code.  
  Note that the code execution environment does not support interactive input.  
- If the tool fails to run or the code does not execute correctly,  
  never assume that it has returned the correct result and continue reasoning based on it!  
  The correct approach is to analyze the cause of the error and try to fix it!  
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
    society: ExcelRolePalying,
    round_limit: int = 15,
) -> Tuple[str, List[dict], dict]:
    overall_completion_token_count = 0
    overall_prompt_token_count = 0

    chat_history = []
    init_prompt = """
    Now please give me instructions to solve over overall task step by step. If the task requires some specific knowledge, please instruct me to use tools to complete the task.
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

    # Create models for different components using Azure OpenAI
    base_model_config = {
        "model_platform": ModelPlatformType.AZURE,
        "model_type": os.getenv("AZURE_OPENAI_MODEL_TYPE"),
        "model_config_dict": ChatGPTConfig(temperature=0.01, max_tokens=4096).as_dict(),
    }


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
        output_language="English"
    )

    return society


def main():
    # Example question

    default_task = """Please help analyze the file `./data/admission_en.xlsx` by:
            - Calculating the number of admitted students, as well as the highest and lowest scores for each college
            - Plotting this information in a single chart: use a bar chart for the number of admitted students, and line charts for the highest and lowest scores
            - Saving the generated chart as `vis_en.png` in the current directory"""

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
