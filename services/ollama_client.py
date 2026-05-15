import json
from typing import Generator
import requests

from services.config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_KEEP_ALIVE


def stream_chat(messages: list[dict]) -> Generator[str, None, None]:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "keep_alive": OLLAMA_KEEP_ALIVE,
    }
    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=OLLAMA_TIMEOUT) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    yield chunk
    except requests.exceptions.ConnectionError:
        yield "\n[Erro: Ollama não está rodando. Execute `ollama serve` no terminal.]"
    except requests.exceptions.Timeout:
        yield "\n[Erro: Ollama demorou demais para responder. Tente novamente.]"
    except Exception as e:
        yield f"\n[Erro inesperado: {e}]"


def warmup():
    """Fire a lightweight request so Ollama pre-loads the model."""
    try:
        requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "messages": [{"role": "user", "content": "ok"}], "stream": False},
            timeout=5,
        )
    except Exception:
        pass
