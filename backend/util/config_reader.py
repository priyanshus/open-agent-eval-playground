import json
import os
from pathlib import Path


def _default_config_path() -> Path:
    path = os.environ.get("CONFIG_PATH")
    if path:
        return Path(path)
    return Path(__file__).resolve().parent.parent.parent / "config.json"


def read_config(path: Path | None = None) -> dict:
    config_path = path or _default_config_path()
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def get_llm_config(path: Path | None = None) -> dict:
    config = read_config(path)
    llm = config.get("llm") or {}
    model_name = llm.get("model_name")
    if not model_name:
        raise ValueError(
            "Config must contain llm.model_name"
        )
    return {"model_name": model_name}
