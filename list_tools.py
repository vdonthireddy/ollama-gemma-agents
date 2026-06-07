#!/usr/bin/env python3
import json

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

if __name__ == "__main__":
    print(json.dumps(TOOLS, indent=2))
