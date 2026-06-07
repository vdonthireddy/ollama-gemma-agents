import ollama

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the internet/web for latest information on a given query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to search the web for."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def perform_web_search(query: str) -> list:
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            raw_results = ddgs.text(query, max_results=4)
            results = []
            for r in raw_results:
                results.append({
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")
                })
            return results
    except Exception as e:
        print(f"Web search error: {e}")
        return []

def check_for_search_tool_call(messages: list, model_name: str) -> tuple[bool, str]:
    try:
        # Call ollama.chat with the message history and tool definition to see if it triggers search
        response = ollama.chat(
            model=model_name,
            messages=messages,
            tools=TOOLS,
            options={"temperature": 0.0}
        )
        
        tool_calls = getattr(response.message, "tool_calls", None)
        if tool_calls:
            for call in tool_calls:
                if call.function.name == "search_web":
                    query = call.function.arguments.get("query", "")
                    return True, query
        return False, ""
    except Exception as e:
        print(f"Error checking search tool call: {e}")
        return False, ""

def build_tool_messages(search_query: str, results: list) -> list[dict]:
    """
    Constructs the assistant tool call message and corresponding tool response message.
    """
    if not results:
        return []
        
    context = ""
    for i, r in enumerate(results, 1):
        context += f"[{i}] Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}\n\n"

    assistant_tool_msg = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "arguments": {"query": search_query}
                }
            }
        ]
    }
    
    tool_response_msg = {
        "role": "tool",
        "name": "search_web",
        "content": f"Search Results for '{search_query}':\n\n{context}"
    }
    
    return [assistant_tool_msg, tool_response_msg]
