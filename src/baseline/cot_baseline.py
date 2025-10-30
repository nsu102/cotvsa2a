import os
import sys
from typing import Dict, Optional
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.openrouter_client import OpenRouterClient

load_dotenv()

class CoTBaseline:
    def __init__(self, model_name: str, dataset: str, use_cot: bool = True):
        self.model_name = model_name
        self.dataset = dataset
        self.use_cot = use_cot

        if use_cot:
            key_name = f"OPENROUTER_API_KEY_COT_{model_name.upper()}"
            app_name = f"cot_{dataset}"
        else:
            key_name = f"OPENROUTER_API_KEY_NO_COT_{model_name.upper()}"
            app_name = f"no_cot_{dataset}"

        api_key = os.getenv(key_name)
        if not api_key:
            raise ValueError(f"Missing API key: {key_name}")

        self.client = OpenRouterClient(api_key, model_name, app_name=app_name)

    def run(self, question: str, context: Optional[str] = None) -> Dict:
        context_block = f"\nContext: {context}\n" if context else ""

        if self.use_cot:
            prompt = f"""You are an expert QA/math assistant.

{context_block}
Question: {question}

Think step by step.

After your reasoning, provide the final answer.
Format: Answer: [your answer]"""
        else:
            prompt = f"""You are an expert QA/math assistant.

{context_block}
Question: {question}

Provide ONLY the final answer. no explanation or reasoning.

Format: Answer: [your answer]"""

        if self.dataset == "math500_algebra":
            max_tokens = 4096 
        else:
            max_tokens = 2048

        response = self.client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens
        )

        return {
            "answer": response.content,
            "total_tokens": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }

    def close(self):
        self.client.close()
