from typing import Dict, Any
import logging
import json
from src.shared.a2a_card import A2ACard, TaskCard
from ..llm_client import get_llm_client

logger = logging.getLogger(__name__)

PLANNER_INSTRUCTION = """Problem: {problem}

Return JSON:
{{
  "analysis": "brief analysis",
  "steps": [{{"solver": "solver_agent", "inputs": {{"problem": "{problem}", "hint": "hint"}}}}]
}}"""


def planner_agent(request: Dict[str, Any]) -> Dict[str, Any]:
    problem = request["problem"]
    model = request.get("model", "claude")
    dataset = request.get("dataset", "math500")

    client = get_llm_client("planner", model, dataset)

    messages = [
        {"role": "user", "content": PLANNER_INSTRUCTION.format(problem=problem)}
    ]

    response = client.chat_completion(messages, temperature=0.3)

    cards = []
    card = TaskCard.create(
        sender="controller",
        recipient="planner",
        task_description="Analyze problem and create strategy",
        context={"problem": problem}
    )
    cards.append(card.to_dict())

    try:
        plan_text = response.content.strip()

        if "```json" in plan_text:
            plan_text = plan_text.split("```json")[1].split("```")[0].strip()
        elif "```" in plan_text:
            plan_text = plan_text.split("```")[1].split("```")[0].strip()

        plan = json.loads(plan_text)

        logger.info(f"📋 Planner: Created execution plan")

        result_card = A2ACard(
            sender="planner",
            recipient="controller",
            message_type="result",
            content=json.dumps(plan),
            metadata={
                "status": "success",
                "tokens": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
        )
        cards.append(result_card.to_dict())

        plan["cards"] = cards
        plan["tokens"] = response.usage.total_tokens
        plan["prompt_tokens"] = response.usage.prompt_tokens
        plan["completion_tokens"] = response.usage.completion_tokens

        return plan

    except Exception as e:
        logger.error(f"Failed to parse plan: {e}")
        return {
            "steps": [
                {"solver": "solver_agent", "inputs": {"problem": problem}}
            ],
            "cards": cards,
            "tokens": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }
    finally:
        client.close()
