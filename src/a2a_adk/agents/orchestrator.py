from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class A2ARuntime:
    def __init__(self):
        self.agents = {}

    def register(self, name: str, agent_func):
        self.agents[name] = agent_func

    def call(self, agent_name: str, inputs: Dict[str, Any]) -> Any:
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        return self.agents[agent_name](inputs)


_runtime = None

def init_runtime():
    global _runtime
    if _runtime is None:
        _runtime = A2ARuntime()
    return _runtime

def get_runtime():
    global _runtime
    if _runtime is None:
        _runtime = init_runtime()
    return _runtime


def orchestrator_agent(
    problem: str,
    model: str = "claude",
    dataset: str = "math500"
) -> Dict[str, Any]:
    logger.info("🧭 Orchestrator: Received math problem")

    runtime = get_runtime()

    plan = runtime.call("planner_agent", {
        "problem": problem,
        "model": model,
        "dataset": dataset
    })

    all_cards = plan.get("cards", [])
    total_tokens = plan.get("tokens", 0)
    total_prompt_tokens = plan.get("prompt_tokens", 0)
    total_completion_tokens = plan.get("completion_tokens", 0)

    for step in plan.get("steps", []):
        solver_name = step["solver"]
        inputs = step["inputs"]
        inputs["model"] = model
        inputs["dataset"] = dataset

        if solver_name == "planner_agent":
            continue

        from src.shared.a2a_card import TaskCard
        task_card = TaskCard.create(
            sender="planner",
            recipient=solver_name,
            task_description="Solve problem with hint",
            context={"hint": inputs.get("hint", "")}
        )
        all_cards.append(task_card.to_dict())

        result = runtime.call(solver_name, inputs)

        if "card" in result:
            all_cards.append(result["card"])

        total_tokens += result.get("tokens", 0)
        total_prompt_tokens += result.get("prompt_tokens", 0)
        total_completion_tokens += result.get("completion_tokens", 0)

        final_answer = result.get("answer", "")

    return {
        "final_answer": final_answer,
        "answer": final_answer,
        "cards": all_cards,
        "total_tokens": total_tokens,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens
    }
