import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")

# Requests timeout: connect + read
AI_CONNECT_TIMEOUT = float(os.getenv("AI_CONNECT_TIMEOUT", "10"))
AI_TIMEOUT = float(os.getenv("AI_TIMEOUT", "300"))

MAX_CONTEXT_CHARS = int(os.getenv("AI_MAX_CONTEXT_CHARS", "6000"))
NUM_PREDICT = int(os.getenv("AI_NUM_PREDICT", "400"))

OPENAI_LIKE_PREFIXES = ("gpt-", "o1-", "text-", "chatgpt-")


def ai_generate(system_text, user_text, model="gpt-4o-mini", temperature=0.2):
    system_text = system_text or ""
    user_text = user_text or ""

    if len(system_text) > MAX_CONTEXT_CHARS:
        system_text = system_text[:MAX_CONTEXT_CHARS] + "\n\n[Context truncated due to length.]"

    ollama_model = model or DEFAULT_OLLAMA_MODEL
    if isinstance(ollama_model, str) and ollama_model.startswith(OPENAI_LIKE_PREFIXES):
        ollama_model = DEFAULT_OLLAMA_MODEL

    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": ollama_model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
        "options": {
            "temperature": float(temperature),
            "num_predict": int(NUM_PREDICT),   # limit output length (faster)
        }
    }

    try:
        resp = requests.post(url, json=payload, timeout=(AI_CONNECT_TIMEOUT, AI_TIMEOUT))
        resp.raise_for_status()
        data = resp.json()
        content = (data.get("message") or {}).get("content") or ""
        return content.strip() or "I couldn't generate a reply right now. Please try again."

    except requests.exceptions.ReadTimeout:
        return (
            "AI is taking too long on this PC (timeout). Try again or use a smaller model "
            "(phi3:mini) and reduce context."
        )
    except requests.exceptions.ConnectionError:
        return (
            "AI is unavailable because Ollama is not running.\n"
            "Start Ollama and make sure http://127.0.0.1:11434 is reachable."
        )
    except requests.HTTPError:
        try:
            err = resp.text
        except Exception:
            err = "Unknown HTTP error"
        return (
            "AI error from Ollama.\n"
            f"Details: {err}\n\n"
            f"Make sure the model is pulled: ollama pull {DEFAULT_OLLAMA_MODEL}"
        )
    except Exception as e:
        return f"AI error: {str(e)}"