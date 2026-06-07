import os
import json
import ollama
from tools import TOOLS, TOOL_REGISTRY
from dotenv import load_dotenv

load_dotenv()

# Ensure local connection works reliably on macOS (avoiding IPv6 resolution issues)
os.environ.setdefault("OLLAMA_HOST", os.getenv("OLLAMA_HOST", "127.0.0.1"))

from logger import log_info, log_error

def check_and_run_tools(messages: list, model_name: str, session_name: str = "default") -> tuple[list[dict], dict[str, any]]:
    """
    Checks if the model requests any tool calls. If yes, executes them using the TOOL_REGISTRY,
    and returns:
      1. A list of tool messages (assistant tool_calls & tool role responses) to append to the chat history.
      2. A dictionary of tool execution results mapped by tool name.
    """
    try:
        log_info(session_name, "[LLM Call] Checking if the model requests any tool calls...")
        response = ollama.chat(
            model=model_name,
            messages=messages,
            tools=TOOLS,
            options={"temperature": 0.0}
        )
        
        tool_calls = getattr(response.message, "tool_calls", None)
        if not tool_calls:
            log_info(session_name, "No tool calls requested by the model.")
            return [], {}
            
        log_info(session_name, f"Model requested {len(tool_calls)} tool call(s): {[c.function.name for c in tool_calls]}")
        tool_messages = []
        tool_results = {}
        
        # Build the assistant's decision to call the tools
        assistant_tool_msg = {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                } for call in tool_calls
            ]
        }
        tool_messages.append(assistant_tool_msg)
        
        # Execute each tool call
        for call in tool_calls:
            func_name = call.function.name
            args = call.function.arguments or {}
            
            if func_name in TOOL_REGISTRY:
                log_info(session_name, f"Executing tool '{func_name}' with args: {args}")
                func = TOOL_REGISTRY[func_name]
                result = func(**args, session_name=session_name)
                tool_results[func_name] = result
                
                # Extract pre-formatted context if returned by the tool module, else serialize
                if isinstance(result, dict) and "content" in result:
                    content = result["content"]
                else:
                    content = json.dumps(result)
                    
                tool_response_msg = {
                    "role": "tool",
                    "name": func_name,
                    "content": content
                }
                tool_messages.append(tool_response_msg)
                log_info(session_name, f"Tool '{func_name}' execution completed successfully.")
                
        return tool_messages, tool_results
    except Exception as e:
        log_error(session_name, f"Error in check_and_run_tools: {e}")
        return [], {}
