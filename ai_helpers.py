
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:1b"

def generate_ai_response(
    prompt,
    timeout=300,
    json_mode=False,
    num_predict=None
):
    """Send a prompt to Ollama and return its response."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    if json_mode:
        payload["format"] = "json"

    if num_predict is not None:
        payload["options"] = {
            "num_predict": num_predict
        }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=timeout
    )
    response.raise_for_status()
    return response.json()["response"]

