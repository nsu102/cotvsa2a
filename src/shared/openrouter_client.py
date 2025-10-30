import httpx
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@dataclass
class LLMResponse:
    content: str
    usage: TokenUsage
    model: str

class OpenRouterClient:
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    MODELS = {
        "claude": "anthropic/claude-haiku-4.5",
        "gpt": "openai/gpt-5-mini"
    }

    def __init__(self, api_key: str, model_name: str, app_name: str = "cotvsa2a"):
        self.api_key = api_key
        self.model = self.MODELS.get(model_name, model_name)
        self.app_name = app_name
        self.client = httpx.Client(timeout=120.0)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": f"https://github.com/nsu102/cotvsa2a/{self.app_name}",
            "X-Title": self.app_name
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = self.client.post(
            self.BASE_URL,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            print(f"\n[ERROR] OpenRouter API {response.status_code}")
            print(f"Request model: {self.model}")
            print(f"Response: {response.text}")

        response.raise_for_status()

        data = response.json()

        usage_data = data.get("usage", {})
        usage = TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0)
        )

        content = data["choices"][0]["message"]["content"]

        return LLMResponse(
            content=content,
            usage=usage,
            model=self.model
        )

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
