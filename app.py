import json
import ollama
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from search_agent import check_for_search_tool_call, build_tool_messages, perform_web_search, TOOLS

app = FastAPI(title="GemmaJnana Gateway")

# Enable CORS for the frontend chat client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = "gemma4:e4b"

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    temperature: float = 0.7

@app.get("/health")
def health_check():
    try:
        models = [m.model for m in ollama.list().models]
        if any(MODEL_NAME in name for name in models):
            return {"status": "healthy", "model": MODEL_NAME}
        return {"status": "warning", "warning": f"Model {MODEL_NAME} not loaded."}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/chat")
def chat_completion(request: ChatRequest):
    try:
        messages_list = [msg.model_dump() for msg in request.messages]
        needs_search, search_query = check_for_search_tool_call(messages_list, MODEL_NAME)

        results = []
        if needs_search and search_query:
            results = perform_web_search(search_query)

        modified_messages = list(messages_list)
        if results:
            modified_messages.extend(build_tool_messages(search_query, results))

        response = ollama.chat(
            model=MODEL_NAME,
            messages=modified_messages,
            tools=TOOLS,
            options={"temperature": request.temperature}
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    def event_generator():
        try:
            messages_list = [msg.model_dump() for msg in request.messages]
            needs_search, search_query = check_for_search_tool_call(messages_list, MODEL_NAME)

            results = []
            if needs_search and search_query:
                yield f"data: {json.dumps({'status': 'searching', 'query': search_query})}\n\n"
                results = perform_web_search(search_query)
                yield f"data: {json.dumps({'status': 'results', 'results': results})}\n\n"

            modified_messages = list(messages_list)
            if results:
                modified_messages.extend(build_tool_messages(search_query, results))

            stream = ollama.chat(
                model=MODEL_NAME,
                messages=modified_messages,
                tools=TOOLS,
                stream=True,
                options={"temperature": request.temperature}
            )
            for chunk in stream:
                content = chunk.message.content
                done = getattr(chunk, "done", False)
                yield f"data: {json.dumps({'content': content, 'done': done})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
