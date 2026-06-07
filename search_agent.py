import os
import json
import ollama
from tools import TOOLS, TOOL_REGISTRY

# Ensure local connection works reliably on macOS (avoiding IPv6 resolution issues)
os.environ.setdefault("OLLAMA_HOST", "127.0.0.1")

def check_and_run_tools(messages: list, model_name: str) -> tuple[list[dict], dict[str, any]]:
    """
    Checks if the model requests any tool calls. If yes, executes them using the TOOL_REGISTRY,
    and returns:
      1. A list of tool messages (assistant tool_calls & tool role responses) to append to the chat history.
      2. A dictionary of tool execution results mapped by tool name.
    """
    try:
        response = ollama.chat(
            model=model_name,
            messages=messages,
            tools=TOOLS,
            options={"temperature": 0.0}
        )
        
        tool_calls = getattr(response.message, "tool_calls", None)
        if not tool_calls:
            return [], {}
            
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
                func = TOOL_REGISTRY[func_name]
                result = func(**args)
                
                # Format response context
                if func_name == "search_web":
                    query = args.get("query", "")
                    tool_results[func_name] = {"query": query, "results": result}
                    
                    context = ""
                    for i, r in enumerate(result, 1):
                        context += f"[{i}] Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}\n\n"
                    content = f"Search Results for '{query}':\n\n{context}"
                else:
                    tool_results[func_name] = result
                    content = json.dumps(result)
                    
                tool_response_msg = {
                    "role": "tool",
                    "name": func_name,
                    "content": content
                }
                tool_messages.append(tool_response_msg)
                
        return tool_messages, tool_results
    except Exception as e:
        print(f"Error in check_and_run_tools: {e}")
        return [], {}
