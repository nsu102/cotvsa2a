from typing import Dict, Any
import logging
from src.shared.a2a_card import ResultCard
from ..llm_client import get_llm_client

logger = logging.getLogger(__name__)

SOLVER_INSTRUCTION = """{problem}
{hint}

dont include any analysis or reasoning just follow the steps
Final answer only (no steps): """


def solver_agent(inputs: Dict[str, Any]) -> Dict[str, Any]:
    problem = inputs["problem"]
    hint = inputs.get("hint", "")
    model = inputs.get("model", "claude")
    dataset = inputs.get("dataset", "math500")

    hint_text = f"Hint: {hint}" if hint else ""

    client = get_llm_client("solver", model, dataset)

    messages = [
        {"role": "user", "content": SOLVER_INSTRUCTION.format(problem=problem, hint=hint_text)}
    ]

    response = client.chat_completion(messages, temperature=0.0, max_tokens=2000)

    answer = response.content.strip()
    logger.info(f"🧮 Solver result: {answer[:100]}...")

    card = ResultCard.create(
        sender="solver",
        recipient="controller",
        result=answer,
        metadata={
            "tokens": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }
    )

    client.close()

    return {
        "answer": answer,
        "card": card.to_dict(),
        "tokens": response.usage.total_tokens,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens
    }
