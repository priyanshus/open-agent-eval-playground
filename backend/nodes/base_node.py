
from langchain_core.language_models import BaseChatModel

from backend.schema.models import State


class BaseNode:
    def __init__(self, llm_client: BaseChatModel):
        self._llm_client = llm_client

    def __call__(self, state:State):
        raise NotImplementedError