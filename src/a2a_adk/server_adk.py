import os
import sys
import json
import re
from typing import Optional, Dict
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from a2a_adk.agents import create_planner_agent, create_solver_agent

load_dotenv()

app = Starlette(debug=True)


def extract_json_action(text: str) -> Optional[Dict]:
    """Extract JSON action from text"""
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

    if "call_solver" in content_lower:
        subtask_patterns = [
            r'["\']subtask["\']\s*:\s*["\']([^"\']+)["\']',
            r'subtask["\s:]+([^"\n}{]+)',
        ]
        for pattern in subtask_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                subtask = match.group(1).strip()
                if subtask:
                    return {"action": "call_solver", "subtask": subtask}

    return None


async def a2a_run(request: Request):
    """A2A endpoint for agent execution"""
    try:
        data = await request.json()

        question = data.get("question")
        context = data.get("context")
        model_name = data.get("model_name")
        dataset = data.get("dataset")

        planner = create_planner_agent(model_name, dataset)
        solver = create_solver_agent(model_name, dataset)

        steps = []
        total_tokens = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0

        plan_result = planner.generate(question, context)
        steps.append({
            "turn": 1,
            "agent": "planner",
            "content": plan_result["content"],
            "tokens": plan_result["usage"]["total_token_count"]
        })

        total_tokens += plan_result["usage"]["total_token_count"]
        total_prompt_tokens += plan_result["usage"]["prompt_token_count"]
        total_completion_tokens += plan_result["usage"]["candidates_token_count"]

        action_data = extract_json_action(plan_result["content"])
        subtask = action_data.get("subtask", question) if action_data else question

        solve_result = solver.generate(subtask, question, context)
        steps.append({
            "turn": 1,
            "agent": "solver",
            "content": solve_result["content"],
            "tokens": solve_result["usage"]["total_token_count"]
        })

        total_tokens += solve_result["usage"]["total_token_count"]
        total_prompt_tokens += solve_result["usage"]["prompt_token_count"]
        total_completion_tokens += solve_result["usage"]["candidates_token_count"]

        final_answer = solve_result["content"]

        planner.close()
        solver.close()

        return JSONResponse({
            "answer": final_answer,
            "total_tokens": total_tokens,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "steps": steps,
            "cards": []
        })

    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"\n[SERVER ERROR] {error_detail}")
        return JSONResponse(
            {"detail": error_detail},
            status_code=500
        )


async def health(request: Request):
    """Health check endpoint"""
    return JSONResponse({"status": "ok"})


routes = [
    Route("/a2a/run", a2a_run, methods=["POST"]),
    Route("/health", health, methods=["GET"]),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
