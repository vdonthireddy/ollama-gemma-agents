SCHEMA = {
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

def handler(query: str) -> list:
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
