import json
import os


CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"
)
CONFIG_PATH = os.path.join(CONFIG_DIR, "api_config.json")


def load_api_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {
            "api_base": "https://api.openai.com/v1",
            "api_key": "",
            "model": "gpt-4o-mini",
        }

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        return {
            "api_base": "https://api.openai.com/v1",
            "api_key": "",
            "model": "gpt-4o-mini",
        }

    config.setdefault("api_base", "https://api.openai.com/v1")
    config.setdefault("api_key", "")
    config.setdefault("model", "gpt-4o-mini")
    return config


def save_api_config(api_base: str, api_key: str, model: str):
    os.makedirs(CONFIG_DIR, exist_ok=True)

    config = {
        "api_base": api_base,
        "api_key": api_key,
        "model": model,
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
