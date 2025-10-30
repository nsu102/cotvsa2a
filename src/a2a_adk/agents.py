import os
from typing import Optional, Dict
from dotenv import load_dotenv
from .openrouter_adapter import create_openrouter_model

load_dotenv()


class PlannerAgent:
    """Planner agent using OpenRouter model"""

    def __init__(self, model_name: str, dataset: str):
        self.model_name = model_name
        self.dataset = dataset

        api_key_name = f"OPENROUTER_API_KEY_A2A_PLAN_{model_name.upper()}"
        api_key = os.getenv(api_key_name)
        if not api_key:
            raise ValueError(f"Missing API key: {api_key_name}")

        self.model = create_openrouter_model(
            model_name=model_name,
            api_key=api_key,
            app_name=f"a2a_planner_{dataset}"
        )

        self.name = "planner"
        self.description = "Planning agent that breaks down tasks"

    def generate(self, question: str, context: Optional[str] = None) -> Dict:
        """Generate planner response"""

        context_section = f"\nContext: {context}\n" if context else ""

        prompt = f"""You are a planning agent in an A2A system.
{context_section}
Question: {question}

Identify ONE key subtask for the solver agent.

Respond in JSON only:
{{"action": "call_solver", "subtask": "<main computation or reasoning needed>"}}"""

        contents = [{"role": "user", "parts": [{"text": prompt}]}]

        config = {
            "temperature": 0.3,
            "max_output_tokens": 256
        }

        response = self.model.generate_content(contents, config)

        return {
            "content": response.text,
            "usage": response.usage_metadata
        }

    def close(self):
        self.model.close()


class SolverAgent:
    """Solver agent using OpenRouter model"""

    def __init__(self, model_name: str, dataset: str):
        self.model_name = model_name
        self.dataset = dataset

        api_key_name = f"OPENROUTER_API_KEY_A2A_SOLVER_{model_name.upper()}"
        api_key = os.getenv(api_key_name)
        if not api_key:
            raise ValueError(f"Missing API key: {api_key_name}")

        self.model = create_openrouter_model(
            model_name=model_name,
            api_key=api_key,
            app_name=f"a2a_solver_{dataset}"
        )

        self.name = "solver"
        self.description = "Solver agent that executes tasks"

    def generate(
        self,
        subtask: str,
        question: str,
        context: Optional[str] = None
    ) -> Dict:
        """Generate solver response"""

        context_block = f"\nContext (search carefully):\n{context}\n" if context else ""

        prompt = f"""You are a solver agent.

Task: {subtask}
{context_block}
Original question: {question}

Provide a concise answer (one sentence or number).

Answer:"""

        contents = [{"role": "user", "parts": [{"text": prompt}]}]

        config = {
            "temperature": 0.3,
            "max_output_tokens": 512
        }

        response = self.model.generate_content(contents, config)

        return {
            "content": response.text,
            "usage": response.usage_metadata
        }

    def close(self):
        self.model.close()


def create_planner_agent(model_name: str, dataset: str) -> PlannerAgent:
    """Factory function for planner agent"""
    return PlannerAgent(model_name, dataset)


def create_solver_agent(model_name: str, dataset: str) -> SolverAgent:
    """Factory function for solver agent"""
    return SolverAgent(model_name, dataset)
