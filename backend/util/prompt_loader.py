from pathlib import Path

from backend.schema.models import State, IntentType


def _prompts_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "prompts"


def get_prompt(name: str) -> str:
    path = _prompts_dir() / f"{name}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def get_system_prompt(self, state: State) -> str:
    match state.intent:
        case IntentType.TRAVEL_PLANNING:
            return get_prompt(
                f"{state.intent.value}/extract_preferences"
            )
        case IntentType.FLIGHT_BOOKING:
            return get_prompt(
                f"{state.intent.value}/extract_preferences"
            )
        case _:
            raise ValueError(
                f"No extraction prompt for intent: {state.intent}"
            )
