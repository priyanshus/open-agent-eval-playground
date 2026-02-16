# Open Agent Evaluation Playground

A minimal agentic system built with LangChain to experiment with routing, tool execution, observability and evaluation using open-source tools.

At present, it has:
- Deterministic router
- Structured execution plan
- Tool-based API calls
- Centralized executor
- Langfuse Integration for Observability

## Architecture
User Query → Router → Execution Plan → Executor → Tools → LLM (final response)

## How to Run
```
cd frontend
npm install
npm run dev

uvicorn backend.main:app --host 0.0.0.0 --port 8080   
```