from pathlib import Path
from typing import Sequence

from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI

from util.config_reader import get_llm_config

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def create_llm_client(
    config_path: Path | None = None,
    callbacks: Sequence[BaseCallbackHandler] | None = None,
) -> ChatOpenAI:
    llm_config = get_llm_config(config_path)
    return ChatOpenAI(
        base_url=OPENROUTER_BASE_URL,
        model=llm_config["model_name"],
        temperature=0.2,
        max_tokens=5000,
        callbacks=list(callbacks) if callbacks else None,
    )
