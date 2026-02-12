from pathlib import Path


def _prompts_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "prompts"


def get_prompt(name: str) -> str:
    path = _prompts_dir() / f"{name}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()
