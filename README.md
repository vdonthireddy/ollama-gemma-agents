# GemmaJnana

![GemmaJnana Banner](./images/linkedin_banner_v3.png)

A local development stack to download, serve, and interact with Google's **Gemma 4 (Effective 4B)** model using **Ollama** and a **FastAPI** gateway. The package comes with a beautiful, fully animated chat playground UI.

---

## Project Architecture Flow

Below is the visual flow of the GemmaJnana local architecture.

![Architecture Flow](./images/architecture_flow.png)

### Data Flow Diagram

```mermaid
graph TD
    Client[Browser UI: index.html] <-->|HTTP/SSE| Backend[FastAPI Gateway: app.py]
    Backend <-->|Local API Port 11434| Ollama[Ollama Server]
    Ollama <-->|Local Inference| Model[(Google Gemma 4 Model)]
    Backend -.->|DuckDuckGo Search| Internet[Internet / Web Search]
```

### Agentic Search Call Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Client as "Browser Client"
    participant App as "app.py"
    participant Agent as "search_agent.py"
    participant Ollama as "Ollama Service"
    participant Web as "Internet Search"

    Client->>App: POST /chat/stream with history
    App->>Agent: check_for_search_tool_call
    Agent->>Ollama: ollama.chat with TOOLS schema
    Ollama-->>Agent: Returns tool_calls if search needed
    
    alt Search Needed
        App->>Agent: perform_web_search
        Agent->>Web: Query web search
        Web-->>Agent: Returns snippets and links
        App->>Agent: build_tool_messages
        Agent-->>App: Returns assistant and tool messages
        App->>App: Append tool messages to history
    end
    
    App->>Ollama: ollama.chat with history and tools
    Ollama-->>App: Stream final cited response
    App-->>Client: Stream content and citations
```

### Components Description

*   **`start.sh`**: The master automation script. It:
    1. Checks if Ollama is installed and automatically updates it to the latest version if needed.
    2. Starts the Ollama service.
    3. Verifies and pulls the `gemma4:e4b` model.
    4. Automatically verifies and installs Python dependencies (`fastapi`, `uvicorn`, `ollama`, `ddgs`).
    5. Launches the FastAPI server in the background.
    6. Serves the web interface in the foreground.
*   **`stop.sh`**: Gracefully terminates all background servers (Ollama, FastAPI app, and the lightweight HTTP server).
*   **`app.py`**: A single-file FastAPI gateway extended to support search classification (agentic routing), DuckDuckGo search execution, and search-context injection into the conversation history. It exposes health checks (`/health`), text completions (`/chat`), and SSE-based chunk streaming (`/chat/stream`).
*   **`index.html`**: A premium dark-themed web playground featuring custom typography, responsive design, a bottom-anchored text input with search settings selector (Auto, Always, Off), dynamic searching status cards, and clickable source citation chips.

---

## What you can and cannot do

Before running the application, it is important to understand what local LLMs are good at and where they fail:

| What you CAN do with Local LLMs | What you CANNOT do with Local LLMs |
| :--- | :--- |
| **Complete Privacy**: Since everything is running on your machine itself, your private code, emails, or personal data never goes to any server outside. | **High speed on old hardware**: If your laptop does not have minimum 8GB/16GB RAM or GPU cores (like Apple Silicon or Nvidia), the response will be very slow. |
| **Works 100% Offline**: You can use the model on a flight, train, or when your wifi is down. No active internet is needed after downloading the model. | **Handling massive documents**: Small local models have limited memory (context window) and will forget details if the chat becomes too long. |
| **Live Web Search (New!)**: The agent can automatically query the internet (via DuckDuckGo) for real-time information, render active source cards, and synthesize current responses with citations. | **Very complex logic**: Small models (like 4B parameters) are amazing for normal coding support and general writing, but they struggle with complex math or heavy logic tasks. |
| **Zero Bills**: There is no token cost or monthly subscription. It is fully free of cost. | **Generate images directly**: These local LLMs are text-only. They cannot generate images or diagrams directly (you need separate diffusion models for that). |
| **Fast testing**: You can tweak python backend parameters or system instructions as much as you want without worrying about API limits. | |
| **Generate text and code**: Write summaries, emails, clean python scripts, and format tables easily. | |

---

## Agentic Web Search Features

GemmaJnana now features a robust agentic search module:
1. **Automatic Routing**: The local Gemma model natively decides if the query needs live internet search based on the query and conversation history, resolving relative terms contextually.
2. **Dynamic UI Indicators**: The web client streams the search status in real-time. When searching, a pulsing loading state is shown. Once results are fetched, active link cards (source chips) are rendered right inside the chat bubble.
3. **Citations & Bibliography**: Answers generated using search are cited in-line (e.g. `[1]`, `[2]`), and a bibliography of sources is displayed at the bottom.

---

## Prerequisites

To run this application, make sure you have:
1.  **macOS** (since automated updates look for `/Applications/Ollama.app`).
2.  **Python 3.x** with the required libraries:
    ```bash
    pip install fastapi uvicorn ollama
    ```

---

## How to Run

1.  **Start the entire service stack**:
    ```bash
    ./start.sh
    ```
    This script will take care of updating Ollama, downloading the model, and launching the servers.

2.  **Open the Web Playground**:
    Navigate to [**`http://localhost:8080`**](http://localhost:8080) in your browser.

3.  **Graceful shutdown**:
    To shut down the web server, press `Ctrl+C` in your terminal. Alternatively, to ensure all background processes (FastAPI, Ollama) are stopped, run:
    ```bash
    ./stop.sh
    ```

---

## Utility Tools

### Listing Available Agent Tools
We provide a simple script that outputs the list of tools defined for the LLM.

Run the script directly:
```bash
python3 list_tools.py
```

---

## API Reference

The FastAPI gateway runs at `http://127.0.0.1:8000` and offers the following endpoints:

*   `GET /health`: Diagnoses connection health and returns active model metadata.
*   `POST /chat`: Completes message requests (non-streaming).
*   `POST /chat/stream`: Initiates an SSE (`text/event-stream`) chat channel.
