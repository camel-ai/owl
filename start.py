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
import argparse
from owl.webapp import main as webapp_main

def main():
    """
    The main entry point for starting the OWL Web Application.
    This script handles command-line arguments for server configuration.
    """
    parser = argparse.ArgumentParser(
        description="""
        OWL: Optimized Workforce Learning for General Multi-Agent Assistance
        in Real-World Task Automation.
        """
    )

    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="The port number to launch the Gradio web server on.",
    )

    parser.add_argument(
        "--share",
        action="store_true",
        help="Set to True to create a public, shareable link for the web UI.",
    )

    args = parser.parse_args()

    # Call the main function from the webapp with the parsed arguments
    webapp_main(port=args.port, share=args.share)


if __name__ == "__main__":
    main()
