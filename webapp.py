#!/usr/bin/env python3
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
[Previous copyright and license headers remain unchanged]

import os
import sys
import shutil
from pathlib import Path

# Add project root to Python path and ensure proper directory structure
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Create and clean output directories
outputs_dir = project_root / "owl" / "outputs"
outputs_dir.mkdir(parents=True, exist_ok=True)

def cleanup_old_outputs(max_age_days=7):
    """Clean up old output files"""
    try:
        current_time = datetime.datetime.now()
        for item in outputs_dir.glob("*"):
            if item.is_file():
                file_time = datetime.datetime.fromtimestamp(item.stat().st_mtime)
                if (current_time - file_time).days > max_age_days:
                    item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    except Exception as e:
        logging.error(f"Error cleaning outputs: {str(e)}")

# Clean up old outputs before starting
cleanup_old_outputs()

from owl.utils.gaia import run_society
from owl.utils.file_toolkit import FileWriteToolkit
import gradio as gr
import time
import json
import logging
import datetime
from typing import Tuple, Optional, Dict, Any
import importlib
from dotenv import load_dotenv, set_key, find_dotenv, unset_key
import threading
import queue
import re
import traceback

[Rest of the imports and constants remain unchanged]

def run_owl(question: str, example_module: str) -> Tuple[str, str, str]:
    """Run the OWL system and return results."""
    global CURRENT_PROCESS

    if not validate_input(question):
        logging.warning("User submitted invalid input")
        return (
            "Please enter a valid question",
            "0",
            "❌ Error: Invalid input question",
        )

    try:
        load_dotenv(find_dotenv(), override=True)
        logging.info(f"Processing question: '{question}', using module: {example_module}")

        # Setup file writing toolkit
        file_toolkit = FileWriteToolkit(output_dir=str(outputs_dir))
        
        if example_module not in MODULE_DESCRIPTIONS:
            logging.error(f"User selected an unsupported module: {example_module}")
            return (
                f"Selected module '{example_module}' is not supported",
                "0",
                "❌ Error: Unsupported module",
            )

        module_path = f"owl.examples.{example_module}"
        try:
            logging.info(f"Importing module: {module_path}")
            module = importlib.import_module(module_path)
        except ImportError as ie:
            logging.error(f"Unable to import module {module_path}: {str(ie)}")
            return (
                f"Unable to import module: {module_path}",
                "0",
                f"❌ Error: Module {example_module} does not exist or cannot be loaded - {str(ie)}",
            )

        if not hasattr(module, "construct_society"):
            logging.error(f"construct_society function not found in module {module_path}")
            return (
                f"construct_society function not found in module {module_path}",
                "0",
                "❌ Error: Module interface incompatible",
            )

        try:
            logging.info("Building society simulation...")
            society = module.construct_society(
                question,
                tools=[*file_toolkit.get_tools()],
                round_limit=25  # Increased round limit
            )
            
            logging.info("Running society simulation...")
            answer, chat_history, token_info = run_society(society)
            
            # Save output files
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_file = outputs_dir / f"summary_{timestamp}.md"
            result_file = outputs_dir / f"result_{timestamp}.txt"
            
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(f"# Task Summary\n\n{answer}\n")
            
            with open(result_file, "w", encoding="utf-8") as f:
                f.write(str(answer))
            
            logging.info("Society simulation completed")
            logging.info(f"Output files created: {summary_file}, {result_file}")
        except Exception as e:
            logging.error(f"Error during simulation: {str(e)}")
            return (
                f"Error occurred during simulation: {str(e)}",
                "0",
                f"❌ Error: {str(e)}",
            )

        if not isinstance(token_info, dict):
            token_info = {}

        completion_tokens = token_info.get("completion_token_count", 0)
        prompt_tokens = token_info.get("prompt_token_count", 0)
        total_tokens = completion_tokens + prompt_tokens

        logging.info(
            f"Processing completed, tokens: completion={completion_tokens}, prompt={prompt_tokens}, total={total_tokens}"
        )

        return (
            answer,
            f"Completion tokens: {completion_tokens:,} | Prompt tokens: {prompt_tokens:,} | Total: {total_tokens:,}",
            "✅ Successfully completed",
        )

    except Exception as e:
        logging.error(f"Uncaught error: {str(e)}")
        traceback.print_exc()
        return (f"Error occurred: {str(e)}", "0", f"❌ Error: {str(e)}")

[Rest of the file content remains unchanged]
