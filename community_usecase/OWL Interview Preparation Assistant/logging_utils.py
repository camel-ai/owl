import os
import logging
import time
import functools
import inspect
import re
from typing import Dict, Any, List, Tuple, Callable, Optional
import queue

# Create a singleton log queue that can be shared between modules
class LogQueueSingleton:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = queue.Queue()
        return cls._instance

# Custom logging wrapper for tools
def log_tool_usage(func):
    """
    Decorator to log when a tool is being used.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        tool_name = func.__name__
        logging.info(f"🔧 TOOL TRIGGERED: {tool_name}")
        try:
            # Sanitize arguments to avoid logging sensitive info
            safe_args = sanitize_args(args)
            safe_kwargs = {k: sanitize_value(v) for k, v in kwargs.items()}
            logging.info(f"🔍 TOOL ARGS: {tool_name} called with {len(safe_kwargs)} parameters")
            
            result = await func(*args, **kwargs)
            
            # Log completion but not the actual result content (might be large or sensitive)
            logging.info(f"✅ TOOL COMPLETED: {tool_name}")
            return result
        except Exception as e:
            logging.error(f"❌ TOOL ERROR: {tool_name} - {str(e)}")
            raise
    return wrapper

# Non-async version for synchronous functions
def log_tool_usage_sync(func):
    """
    Decorator to log when a synchronous tool is being used.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = func.__name__
        logging.info(f"🔧 TOOL TRIGGERED: {tool_name}")
        try:
            # Sanitize arguments to avoid logging sensitive info
            safe_args = sanitize_args(args)
            safe_kwargs = {k: sanitize_value(v) for k, v in kwargs.items()}
            logging.info(f"🔍 TOOL ARGS: {tool_name} called with {len(safe_kwargs)} parameters")
            
            result = func(*args, **kwargs)
            
            # Log completion but not the actual result content (might be large or sensitive)
            logging.info(f"✅ TOOL COMPLETED: {tool_name}")
            return result
        except Exception as e:
            logging.error(f"❌ TOOL ERROR: {tool_name} - {str(e)}")
            raise
    return wrapper

def sanitize_args(args):
    """Sanitize arguments for logging to avoid sensitive data."""
    safe_args = []
    for arg in args:
        safe_args.append(sanitize_value(arg))
    return safe_args

def sanitize_value(value):
    """Sanitize a value for logging."""
    if isinstance(value, str):
        if len(value) > 50:
            return value[:47] + "..."
        return value
    elif isinstance(value, (list, tuple)):
        return f"{type(value).__name__} with {len(value)} items"
    elif isinstance(value, dict):
        return f"dict with {len(value)} items"
    else:
        return f"{type(value).__name__}"

class LoggingToolkitWrapper:
    """
    Wrapper class to add logging to toolkit methods.
    """
    def __init__(self, toolkit):
        self.toolkit = toolkit
        self.toolkit_name = toolkit.__class__.__name__
        logging.info(f"📦 TOOLKIT INITIALIZED: {self.toolkit_name}")
        
    def __getattr__(self, name):
        attr = getattr(self.toolkit, name)
        
        if callable(attr) and not name.startswith('_'):
            if inspect.iscoroutinefunction(attr):
                # It's an async function, wrap it with our async decorator
                return log_tool_usage(attr)
            else:
                # For non-async functions
                @functools.wraps(attr)
                def wrapper(*args, **kwargs):
                    logging.info(f"🔧 TOOL TRIGGERED: {self.toolkit_name}.{name}")
                    try:
                        # Sanitize arguments to avoid logging sensitive info
                        safe_args = sanitize_args(args)
                        safe_kwargs = {k: sanitize_value(v) for k, v in kwargs.items()}
                        logging.info(f"🔍 TOOL ARGS: {name} called with {len(safe_kwargs)} parameters")
                        
                        result = attr(*args, **kwargs)
                        
                        logging.info(f"✅ TOOL COMPLETED: {self.toolkit_name}.{name}")
                        return result
                    except Exception as e:
                        logging.error(f"❌ TOOL ERROR: {self.toolkit_name}.{name} - {str(e)}")
                        raise
                return wrapper
        
        return attr

def wrap_toolkits(toolkits_list):
    """
    Wrap a list of toolkits with logging functionality.
    """
    wrapped_toolkits = []
    for toolkit in toolkits_list:
        wrapped_toolkits.append(LoggingToolkitWrapper(toolkit))
    return wrapped_toolkits
# Find this function in logging_utils.py and replace it with this corrected version

# Enhanced run_society function with logging
def enhanced_run_society(society, verbose=True):
    """
    Enhanced wrapper around the OWL run_society function with detailed logging.
    """
    from owl.utils import run_society as original_run_society
    
    # Log the society setup
    user_role = getattr(society, 'user_role_name', 'User')
    assistant_role = getattr(society, 'assistant_role_name', 'Assistant')
    
    logging.info(f"🚀 STARTING AGENT SOCIETY: {user_role} & {assistant_role}")
    logging.info(f"📝 TASK: {society.task_prompt[:100]}...")
    
    # Log agent initialization
    logging.info(f"🤖 INITIALIZING AGENT: {assistant_role}")
    
    # Add hooks to log message exchanges if possible
    original_send_message = None
    if hasattr(society, 'assistant_agent') and hasattr(society.assistant_agent, 'send_message'):
        original_send_message = society.assistant_agent.send_message
        
        @functools.wraps(original_send_message)
        def logged_send_message(*args, **kwargs):
            logging.info(f"💬 AGENT MESSAGE: {assistant_role} is processing...")
            result = original_send_message(*args, **kwargs)
            logging.info(f"📨 AGENT RESPONSE RECEIVED from {assistant_role}")
            return result
        
        society.assistant_agent.send_message = logged_send_message
    
    # Try to log tool usage if possible
    if hasattr(society, 'assistant_agent') and hasattr(society.assistant_agent, 'tools'):
        tools = getattr(society.assistant_agent, 'tools', [])
        logging.info(f"🧰 AGENT HAS {len(tools)} TOOLS AVAILABLE")
        
        # Attempt to wrap each tool with logging
        for i, tool in enumerate(tools):
            if callable(tool):
                tool_name = getattr(tool, '__name__', f"tool_{i}")
                logging.info(f"🔧 TOOL AVAILABLE: {tool_name}")
    
    # Run the original function
    start_time = time.time()
    try:
        logging.info(f"⏳ RUNNING SOCIETY...")
        # Remove the verbose parameter from the call to original_run_society
        answer, chat_history, token_count = original_run_society(society)
        end_time = time.time()
        duration = end_time - start_time
        
        # Log prompt and completion tokens separately if available
        if isinstance(token_count, dict):
            prompt_tokens = token_count.get('prompt_token_count', 0)
            completion_tokens = token_count.get('completion_token_count', 0)
            logging.info(f"💰 TOKEN USAGE: Prompt={prompt_tokens}, Completion={completion_tokens}, Total={prompt_tokens + completion_tokens}")
        else:
            logging.info(f"💰 TOKEN USAGE: {token_count}")
            
        logging.info(f"✅ AGENT SOCIETY COMPLETED: Duration {duration:.2f}s")
        
        return answer, chat_history, token_count
    except Exception as e:
        logging.error(f"❌ AGENT SOCIETY ERROR: {str(e)}")
        raise
    finally:
        # Restore original method if we modified it
        if original_send_message and hasattr(society, 'assistant_agent'):
            society.assistant_agent.send_message = original_send_message
            
            

# Function to sanitize logs to avoid exposing sensitive information
def sanitize_log(log_message):
    """
    Sanitize log messages to avoid exposing sensitive information like IPs.
    """
    # Simple IP address pattern matching
    ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    sanitized = re.sub(ip_pattern, '[REDACTED_IP]', log_message)
    
    # Redact API keys (common patterns)
    api_key_pattern = r'(api[_-]?key|apikey|key|token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]{20,})["\']?'
    sanitized = re.sub(api_key_pattern, r'\1: [REDACTED_API_KEY]', sanitized, flags=re.IGNORECASE)
    
    # Redact URLs with authentication information
    url_auth_pattern = r'(https?://)([^:@/]+:[^@/]+@)([^\s/]+)'
    sanitized = re.sub(url_auth_pattern, r'\1[REDACTED_AUTH]@\3', sanitized)
    
    return sanitized

# Enhanced StreamlitLogHandler that sanitizes logs
class EnhancedStreamlitLogHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
    def emit(self, record):
        log_entry = self.format(record)
        # Sanitize the log to remove sensitive information
        sanitized_log = sanitize_log(log_entry)
        self.log_queue.put(sanitized_log)

# Add logging to specific OWL functions if possible
# Add this updated function to logging_utils.py

# Add logging to specific OWL functions if possible
def patch_owl_logging():
    """Try to patch specific OWL functions to add logging."""
    try:
        from owl import utils
        
        # If run_society exists in utils, patch it to log
        if hasattr(utils, 'run_society'):
            original_run = utils.run_society
            
            def logged_run_society(*args, **kwargs):
                logging.info("🦉 OWL run_society called")
                try:
                    result = original_run(*args, **kwargs)
                    logging.info("🦉 OWL run_society completed")
                    return result
                except Exception as e:
                    logging.error(f"🦉 OWL run_society error: {str(e)}")
                    raise
            
            # Replace the original function
            utils.run_society = logged_run_society
            logging.info("🦉 OWL run_society patched with logging")
            
        return True
    except ImportError:
        logging.warning("⚠️ Could not patch OWL logging - module not found")
        return False
    except Exception as e:
        logging.warning(f"⚠️ Error patching OWL logging: {str(e)}")
        return False