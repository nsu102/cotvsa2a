from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.openrouter_client import OpenRouterClient
from shared.a2a_card import A2ACardProtocol, TaskCard, ResultCard, ControlCard

load_dotenv()

app = FastAPI(title="A2A Protocol Server")

class A2ARequest(BaseModel):
    question: str
    context: Optional[str] = None
    model_name: str
    dataset: str

class A2AResponse(BaseModel):
    answer: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    steps: List[Dict]
    cards: List[Dict]

def extract_json_action(text: str) -> Optional[Dict]:
    import json
    import re

    json_patterns = [
        r'\{[^{}]*"action"[^{}]*\}',
        r'\{[^{}]*\}',
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match)
                if "action" in data:
                    return data
            except json.JSONDecodeError:
                continue

    content_lower = text.lower()

    if "call_solver" in content_lower or "call solver" in content_lower:
        subtask_patterns = [
            r'["\']subtask["\']\s*:\s*["\']([^"\']+)["\']',
            r'subtask["\s:]+([^"\n}{]+)',
            r'solver[^:]*:\s*["\']?([^"\n}{]+)["\']?',
        ]
        for pattern in subtask_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                subtask = match.group(1).strip()
                if subtask:
                    return {"action": "call_solver", "subtask": subtask}

    if "final_answer" in content_lower or "final answer" in content_lower:
        answer_patterns = [
            r'["\']answer["\']\s*:\s*["\']([^"\']+)["\']',
            r'answer["\s:]+([^"\n}{]+)',
            r'final[^:]*:\s*["\']?([^"\n}{]+)["\']?',
        ]
        for pattern in answer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                answer = match.group(1).strip()
                if answer:
                    return {"action": "final_answer", "answer": answer}

    return None

class A2AAgent:
    def __init__(self, model_name: str, dataset: str):
        self.dataset = dataset
        if dataset == "hotpotqa":
            self.max_turns = 5
        elif dataset == "math500_algebra":
            self.max_turns = 5
        else:
            self.max_turns = 3

        plan_key = f"OPENROUTER_API_KEY_A2A_PLAN_{model_name.upper()}"
        solve_key = f"OPENROUTER_API_KEY_A2A_SOLVER_{model_name.upper()}"

        plan_api_key = os.getenv(plan_key)
        solve_api_key = os.getenv(solve_key)

        if not plan_api_key or not solve_api_key:
            raise ValueError(f"Missing API keys: {plan_key} or {solve_key}")

        self.planner = OpenRouterClient(
            plan_api_key,
            model_name,
            app_name=f"a2a_planner_{dataset}"
        )
        self.solver = OpenRouterClient(
            solve_api_key,
            model_name,
            app_name=f"a2a_solver_{dataset}"
        )

    def run_original(self, question: str, context: Optional[str] = None) -> A2AResponse:
        steps = []
        cards = []
        total_tokens = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0

        conversation_history = []
        final_answer = None

        initial_task_card = A2ACardProtocol.create_task_card(
            from_agent=A2ACardProtocol.CONTROLLER,
            to_agent=A2ACardProtocol.PLANNER,
            task=question,
            context={"dataset": self.dataset, "context": context} if context else {"dataset": self.dataset}
        )
        cards.append(initial_task_card.to_dict())

        context_section = f"\nContext: {context}\n" if context else ""

        initial_prompt = f"""You are a planning agent in an A2A (Agent-to-Agent) system.
{context_section}
Question: {question}

IMPORTANT: Break down this task and delegate subtasks to the solver agent.

You may call the solver multiple times to collect intermediate results.
Each time, respond strictly in JSON (no explanations or extra text):
{{"action": "call_solver", "subtask": "<describe a specific intermediate computation or lookup>"}}

When you have enough information, return:
{{"action": "final_answer", "answer": "<final answer>"}}

In the first turn, you should call the solver unless the answer is immediately obvious.

Provide the JSON action now."""

        conversation_history.append({"role": "user", "content": initial_prompt})

        for turn in range(self.max_turns):
            plan_response = self.planner.chat_completion(
                messages=conversation_history.copy(),
                temperature=0.3,
                max_tokens=512
            )

            steps.append({
                "turn": turn + 1,
                "agent": "planner",
                "content": plan_response.content,
                "tokens": plan_response.usage.total_tokens
            })

            total_tokens += plan_response.usage.total_tokens
            total_prompt_tokens += plan_response.usage.prompt_tokens
            total_completion_tokens += plan_response.usage.completion_tokens

            action_data = extract_json_action(plan_response.content)
            action = action_data.get("action") if action_data else None

            if action_data and action:

                    if action == "final_answer":
                        final_answer = action_data.get("answer", plan_response.content)

                        result_card = A2ACardProtocol.create_result_card(
                            from_agent=A2ACardProtocol.PLANNER,
                            to_agent=A2ACardProtocol.CONTROLLER,
                            result=final_answer,
                            status="completed",
                            metadata={"turn": turn + 1}
                        )
                        cards.append(result_card.to_dict())
                        break
                    elif action == "call_solver":
                        subtask = action_data.get("subtask", "")

                        solver_task_card = A2ACardProtocol.create_task_card(
                            from_agent=A2ACardProtocol.PLANNER,
                            to_agent=A2ACardProtocol.SOLVER,
                            task=subtask,
                            context={"original_question": question, "turn": turn + 1}
                        )
                        cards.append(solver_task_card.to_dict())

                        context_block = f"\nContext (search this carefully):\n{context}\n" if context else ""

                        solver_prompt = f"""You are a solver agent.

Your task: {subtask}
{context_block}
Original question: {question}

Instructions:
1. Complete the specific subtask requested
2. Provide only the minimal answer needed
3. Be extremely concise - one sentence or number
4. If information not found in context, say "Not found"

Your answer:"""

                        solve_response = self.solver.chat_completion(
                            messages=[{"role": "user", "content": solver_prompt}],
                            temperature=0.3,
                            max_tokens=1024
                        )

                        steps.append({
                            "turn": turn + 1,
                            "agent": "solver",
                            "content": solve_response.content,
                            "tokens": solve_response.usage.total_tokens
                        })

                        total_tokens += solve_response.usage.total_tokens
                        total_prompt_tokens += solve_response.usage.prompt_tokens
                        total_completion_tokens += solve_response.usage.completion_tokens

                        solver_result_card = A2ACardProtocol.create_result_card(
                            from_agent=A2ACardProtocol.SOLVER,
                            to_agent=A2ACardProtocol.PLANNER,
                            result=solve_response.content,
                            status="success",
                            metadata={"turn": turn + 1, "tokens": solve_response.usage.total_tokens}
                        )
                        cards.append(solver_result_card.to_dict())

                        conversation_history.append({"role": "assistant", "content": plan_response.content})

                        if turn < self.max_turns - 1:
                            follow_up = f"""Solver result: {solve_response.content}

Now decide. Respond strictly in JSON (no extra text):
- If you need another subtask: {{"action": "call_solver", "subtask": "<next subtask>"}}
- If you can answer now: {{"action": "final_answer", "answer": "<answer>"}}

Provide JSON action:"""
                        else:
                            follow_up = f"""Solver result: {solve_response.content}

Final turn. Provide the answer now in JSON:
{{"action": "final_answer", "answer": "<answer>"}}"""

                        conversation_history.append({"role": "user", "content": follow_up})

            if not action_data:
                if turn == 0:
                    conversation_history.append({"role": "assistant", "content": plan_response.content})
                    conversation_history.append({
                        "role": "user",
                        "content": "ERROR: You must provide a JSON action. Format: {\"action\": \"call_solver\", \"subtask\": \"...\"}"
                    })
                    continue
                else:
                    final_answer = plan_response.content
                    break

            if turn == self.max_turns - 1 and action != "final_answer":
                final_answer = plan_response.content
                break

        if not final_answer:
            final_answer = steps[-1]["content"] if steps else "No answer generated"

        return A2AResponse(
            answer=final_answer,
            total_tokens=total_tokens,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            steps=steps,
            cards=cards
        )

    def run(self, question: str, context: Optional[str] = None) -> A2AResponse:
        steps = []
        cards = []
        total_tokens = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0

        context_section = f"\nContext: {context}\n" if context else ""

        planner_prompt = f"""You are a planning agent in an A2A system.
{context_section}
Question: {question}

Identify ONE key subtask for the solver agent.

Respond in JSON only:
{{"action": "call_solver", "subtask": "<main computation or reasoning needed>"}}"""

        plan_response = self.planner.chat_completion(
            messages=[{"role": "user", "content": planner_prompt}],
            temperature=0.3,
            max_tokens=256
        )

        steps.append({
            "turn": 1,
            "agent": "planner",
            "content": plan_response.content,
            "tokens": plan_response.usage.total_tokens
        })

        total_tokens += plan_response.usage.total_tokens
        total_prompt_tokens += plan_response.usage.prompt_tokens
        total_completion_tokens += plan_response.usage.completion_tokens

        action_data = extract_json_action(plan_response.content)
        subtask = action_data.get("subtask", question) if action_data else question

        context_block = f"\nContext (search carefully):\n{context}\n" if context else ""

        solver_prompt = f"""You are a solver agent.

Task: {subtask}
{context_block}
Original question: {question}

Provide a concise answer (one sentence or number).

Answer:"""

        solve_response = self.solver.chat_completion(
            messages=[{"role": "user", "content": solver_prompt}],
            temperature=0.3,
            max_tokens=512
        )

        steps.append({
            "turn": 1,
            "agent": "solver",
            "content": solve_response.content,
            "tokens": solve_response.usage.total_tokens
        })

        total_tokens += solve_response.usage.total_tokens
        total_prompt_tokens += solve_response.usage.prompt_tokens
        total_completion_tokens += solve_response.usage.completion_tokens

        final_answer = solve_response.content

        return A2AResponse(
            answer=final_answer,
            total_tokens=total_tokens,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            steps=steps,
            cards=cards
        )

    def close(self):
        self.planner.close()
        self.solver.close()

@app.post("/a2a/run", response_model=A2AResponse)
async def run_a2a(request: A2ARequest):
    try:
        agent = A2AAgent(request.model_name, request.dataset)
        response = agent.run(request.question, request.context)
        agent.close()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
