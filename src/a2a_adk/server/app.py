from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv()

from ..agents.orchestrator import orchestrator_agent, init_runtime, get_runtime
from ..agents.planner import planner_agent
from ..agents.solvers import solver_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="A2A Math Solver", version="1.0.0")

runtime = init_runtime()
runtime.register("planner_agent", planner_agent)
runtime.register("solver_agent", solver_agent)


class A2ARequest(BaseModel):
    question: str
    model_name: Optional[str] = "claude"
    dataset: Optional[str] = "math500"


class A2AResponse(BaseModel):
    answer: str
    cards: list
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int


@app.get("/")
def root():
    return {"message": "A2A Math Solver API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/a2a/run", response_model=Dict[str, Any])
def run_a2a(request: A2ARequest):
    try:
        logger.info(f"Received A2A request for model: {request.model_name}, dataset: {request.dataset}")

        result = orchestrator_agent(
            problem=request.question,
            model=request.model_name,
            dataset=request.dataset
        )

        return {
            "answer": result.get("answer", ""),
            "final_answer": result.get("final_answer", ""),
            "cards": result.get("cards", []),
            "total_tokens": result.get("total_tokens", 0),
            "prompt_tokens": result.get("prompt_tokens", 0),
            "completion_tokens": result.get("completion_tokens", 0),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"A2A execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
