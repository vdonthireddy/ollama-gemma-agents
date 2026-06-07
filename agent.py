import os
import json
import ollama
from tools import TOOLS, TOOL_REGISTRY
from dotenv import load_dotenv

load_dotenv()

# Ensure local connection works reliably on macOS (avoiding IPv6 resolution issues)
os.environ.setdefault("OLLAMA_HOST", os.getenv("OLLAMA_HOST", "127.0.0.1"))

from logger import log_info, log_error

def check_and_run_tools(messages: list, model_name: str, session_name: str = "default") -> tuple[list[dict], dict[str, any], int]:
    """
    Checks if the model requests any tool calls in a loop (up to 5 steps) to support sequential/multi-step reasoning.
    Returns:
      1. A list of tool messages (assistant tool_calls & tool responses) to append to history.
      2. A dictionary of executed tool results mapped by tool name.
      3. The number of LLM calls made during checking.
    """
    tool_messages = []
    tool_results = {}
    llm_calls = 0
    current_messages = list(messages)
    
    for iteration in range(5):
        try:
            log_info(session_name, f"[LLM Call] Checking if the model requests any tool calls (iteration {iteration + 1})...")
            llm_calls += 1
            
            response = ollama.chat(
                model=model_name,
                messages=current_messages + tool_messages,
                tools=TOOLS,
                options={"temperature": 0.0}
            )
            
            tool_calls = getattr(response.message, "tool_calls", None)
            if not tool_calls:
                log_info(session_name, f"No more tool calls requested by the model at iteration {iteration + 1}.")
                break
                
            log_info(session_name, f"Model requested {len(tool_calls)} tool call(s) at iteration {iteration + 1}: {[c.function.name for c in tool_calls]}")
            
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
                    
        except Exception as e:
            log_error(session_name, f"Error in check_and_run_tools at iteration {iteration + 1}: {e}")
            break
            
    return tool_messages, tool_results, llm_calls

