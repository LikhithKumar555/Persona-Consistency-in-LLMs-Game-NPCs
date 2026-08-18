
import os
from dotenv import load_dotenv

load_dotenv()

_clients = {}
PROVIDER_CONFIG = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "env_key": "OLLAMA_API_KEY",   
    },
}
def _get_client(provider):
    if provider not in PROVIDER_CONFIG:
        raise ValueError(f"Unknown provider '{provider}'. Configured providers: {list(PROVIDER_CONFIG.keys())}")
    if provider not in _clients:
        import openai
        config = PROVIDER_CONFIG[provider]
        api_key = os.environ.get(config["env_key"], "ollama")
        _clients[provider] = openai.OpenAI(
            api_key=api_key,
            base_url=config["base_url"],
        )
    return _clients[provider]
def get_response(provider, model_name, system_prompt, messages, max_tokens=300): 
    client = _get_client(provider)
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    response = client.chat.completions.create(
        model=model_name,
        max_tokens=max_tokens,
        messages=full_messages,
    )
    content = response.choices[0].message.content
    if content is None:
        finish_reason = response.choices[0].finish_reason
        raise RuntimeError(
            f"Model returned empty content (finish_reason={finish_reason}). "
            f"This can happen with free-tier overload/moderation - usually works on retry."
        )
    return content
