import os
from pathlib import Path


def _load_env_file(path: str = ".env") -> None:
    """Load environment variables from a .env file if present.
    Minimal loader without external dependencies.
    """
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Do not override an already-set variable in the environment
        if key and (key not in os.environ):
            os.environ[key] = value


def get_openai_api_key() -> str:
    """Return the OpenAI API key from environment variables.

    Best practice: do not hardcode secrets in code.
    You can set OPENAI_API_KEY via OS env or in a .env file.
    """
    _load_env_file()
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Configure it as an environment variable "
            "(e.g., PowerShell: $env:OPENAI_API_KEY='...') or set it in .env before starting the server."
        )
    return key


def get_openai_model(default: str = "gpt-4o-mini") -> str:
    """Return the OpenAI model name; default to gpt-4o-mini if not set."""
    _load_env_file()
    return os.getenv("OPENAI_MODEL", default)