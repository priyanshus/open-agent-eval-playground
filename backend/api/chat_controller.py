from dotenv import load_dotenv
from fastapi import APIRouter
from pydantic import BaseModel

load_dotenv()
router = APIRouter()

_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        from backend.app_workflow import IntentClassifierAgent
        from backend.llm.client import create_llm_client
        _agent = IntentClassifierAgent(llm_client=create_llm_client())
        _agent.build_workflow()
    return _agent


class ChatPayload(BaseModel):
    user_query: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    thinking: str
    trajectory: list[str]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatPayload) -> ChatResponse:
    result = _get_agent().invoke(request.user_query, request.session_id or "")
    return ChatResponse(
        response=result["response"],
        thinking=result["thinking"],
        trajectory=result["trajectory"],
    )
