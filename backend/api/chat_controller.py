from dotenv import load_dotenv
from fastapi import APIRouter
from pydantic import BaseModel

from backend.app_workflow import IntentClassifierAgent
from backend.llm.client import create_llm_client

load_dotenv()
router = APIRouter()
agent = IntentClassifierAgent(llm_client=create_llm_client())
agent.build_workflow()

class ChatPayload(BaseModel):
    user_query: str
    session_id: str | None = None


@router.post("/chat")
def chat(request: ChatPayload) -> dict[str, str]:
    """Returns dict with 'response' (AI message) and 'thinking' (AI thinking/reasoning)."""
    return agent.invoke(request.user_query, request.session_id or "")
