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
import importlib
import io
import json
import logging
import os
import sys
from typing import Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from camel.toolkits import BaseToolkit

logger = logging.getLogger(__name__)

sys.path.append(os.getcwd())

custom_port = int(sys.argv[1])

modules_functions = sys.argv[2:]

logger.info(f"Modules and functions: {modules_functions}")

app = FastAPI()


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error_message": str(exc),
        },
    )


for module_function in modules_functions:
    try:
        init_params = dict()
        if "{" in module_function:
            module_function, params = module_function.split("{")
            params = "{" + params
            init_params = json.loads(params)

        module_name, function_name = module_function.rsplit(".", 1)

        logger.info(f"Importing {module_name} and function {function_name}")

        module = importlib.import_module(module_name)
        function = getattr(module, function_name)
        if isinstance(function, type) and issubclass(function, BaseToolkit):
            function = function(**init_params).get_tools()

        if not isinstance(function, list):
            function = [function]

        for func in function:

            @app.post(f"/{func.get_function_name()}")
            async def dynamic_function(data: Dict, func=func):
                redirect_stdout = data.get("redirect_stdout", False)
                if redirect_stdout:
                    sys.stdout = io.StringIO()
                response_data = func.func(*data["args"], **data["kwargs"])
                if redirect_stdout:
                    sys.stdout.seek(0)
                    output = sys.stdout.read()
                    sys.stdout = sys.__stdout__
                    return {
                        "output": json.dumps(response_data),
                        "stdout": output,
                    }
                return {"output": json.dumps(response_data)}

    except (ImportError, AttributeError) as e:
        logger.error(f"Error importing {module_function}: {e}")


if __name__ == "__main__":
    uvicorn.run("__main__:app", host="0.0.0.0", port=custom_port, reload=True)
