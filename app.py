import json
import ollama
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from search_agent import check_and_run_tools, TOOLS

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
        tool_messages, _ = check_and_run_tools(messages_list, MODEL_NAME)

        modified_messages = list(messages_list)
        if tool_messages:
            modified_messages.extend(tool_messages)

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
            tool_messages, tool_results = check_and_run_tools(messages_list, MODEL_NAME)

            if "search_web" in tool_results:
                search_data = tool_results["search_web"]
                yield f"data: {json.dumps({'status': 'searching', 'query': search_data['query']})}\n\n"
                yield f"data: {json.dumps({'status': 'results', 'results': search_data['results']})}\n\n"

            modified_messages = list(messages_list)
            if tool_messages:
                modified_messages.extend(tool_messages)

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
