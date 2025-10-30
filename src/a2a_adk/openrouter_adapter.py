from typing import Dict, List, Optional
import httpx


class OpenRouterModel:
    """Custom model adapter for OpenRouter to use with ADK"""

    MODELS = {
        "claude": "anthropic/claude-3.5-haiku",
        "gpt": "openai/gpt-4o-mini"
    }

    def __init__(self, model_name: str, api_key: str, app_name: str = "adk_a2a"):
        self.model_name = model_name
        self.model = self.MODELS.get(model_name, model_name)
        self.api_key = api_key
        self.app_name = app_name
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.client = httpx.Client(timeout=120.0)

    def generate_content(
        self,
        contents: List[Dict],
        config: Optional[Dict] = None
    ) -> "GenerateContentResponse":
        """
        Generate content using OpenRouter API
        Compatible with ADK's model interface
        """
        messages = self._convert_contents_to_messages(contents)

        temperature = config.get("temperature", 0.7) if config else 0.7
        max_tokens = config.get("max_output_tokens", 2048) if config else 2048

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": f"https://github.com/cotvsa2a/{self.app_name}",
            "X-Title": self.app_name
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = self.client.post(
            self.base_url,
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()

        return GenerateContentResponse(
            text=data["choices"][0]["message"]["content"],
            usage_metadata={
                "prompt_token_count": data["usage"]["prompt_tokens"],
                "candidates_token_count": data["usage"]["completion_tokens"],
                "total_token_count": data["usage"]["total_tokens"]
            }
        )

    def _convert_contents_to_messages(self, contents: List[Dict]) -> List[Dict]:
        """Convert ADK content format to OpenAI message format"""
        messages = []

        for content in contents:
            if isinstance(content, dict):
                role = content.get("role", "user")

                if "parts" in content:
                    text_parts = []
                    for part in content["parts"]:
                        if isinstance(part, dict) and "text" in part:
                            text_parts.append(part["text"])
                        elif isinstance(part, str):
                            text_parts.append(part)

                    text = "\n".join(text_parts)
                else:
                    text = content.get("text", "")

                messages.append({
                    "role": role,
                    "content": text
                })
            elif isinstance(content, str):
                messages.append({
                    "role": "user",
                    "content": content
                })

        return messages

    def close(self):
        self.client.close()


class GenerateContentResponse:
    """Response format compatible with ADK"""

    def __init__(self, text: str, usage_metadata: Dict):
        self.text = text
        self._usage_metadata = usage_metadata
        self.candidates = [Candidate(text)]

    @property
    def usage_metadata(self):
        return self._usage_metadata


class Candidate:
    """Candidate format compatible with ADK"""

    def __init__(self, text: str):
        self.content = Content(text)


class Content:
    """Content format compatible with ADK"""

    def __init__(self, text: str):
        self.parts = [Part(text)]


class Part:
    """Part format compatible with ADK"""

    def __init__(self, text: str):
        self.text = text


def create_openrouter_model(model_name: str, api_key: str, app_name: str = "adk_a2a"):
    """Factory function to create OpenRouter model"""
    return OpenRouterModel(model_name, api_key, app_name)
