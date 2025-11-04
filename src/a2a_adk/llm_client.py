import os
from typing import Dict, Any
from src.shared.openrouter_client import OpenRouterClient

def get_llm_client(agent_type: str, model_name: str = "claude", dataset: str = "math") -> OpenRouterClient:
    env_key_map = {
        "planner_claude": "OPENROUTER_API_KEY_A2A_PLAN_CLAUDE",
        "solver_claude": "OPENROUTER_API_KEY_A2A_SOLVER_CLAUDE",
        "planner_gpt": "OPENROUTER_API_KEY_A2A_PLAN_GPT",
        "solver_gpt": "OPENROUTER_API_KEY_A2A_SOLVER_GPT",
    }

    model_map = {
        "planner_claude": "anthropic/claude-haiku-4.5",
        "solver_claude": "anthropic/claude-haiku-4.5",
        "planner_gpt": "openai/gpt-5-mini",
        "solver_gpt": "openai/gpt-5-mini",
    }

    key_name = f"{agent_type}_{model_name}"
    api_key = os.getenv(env_key_map.get(key_name, env_key_map["planner_claude"]))

    if not api_key:
        raise ValueError(f"Missing API key for {key_name}")

    actual_model = model_map.get(key_name, model_map["solver_claude"])
    app_name = f"a2a_{agent_type}_{dataset}"

    return OpenRouterClient(api_key=api_key, model_name=actual_model, app_name=app_name)
