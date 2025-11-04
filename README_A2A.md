# A2A Math Solver System

Agent-to-Agent protocol implementation for efficient mathematical problem solving.

## Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Orchestrator   │  (Controller)
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌────────┐
│Planner │  │Solver  │
│Agent   │  │Agent   │
└────────┘  └────────┘
```

### Components

1. **Planner Agent**
   - Analyzes problem type
   - Provides solving hint
   - API: `OPENROUTER_API_KEY_A2A_PLAN_CLAUDE/GPT`

2. **Solver Agent**
   - Solves the problem
   - Uses planner's hint
   - API: `OPENROUTER_API_KEY_A2A_SOLVER_CLAUDE/GPT`

3. **Orchestrator**
   - Coordinates communication
   - Tracks tokens
   - Collects A2A cards

## Usage

### Start Server
```bash
python src/a2a_adk/run_server.py
```

### Test System
```bash
python test_a2a_system.py
```

### Run Experiments
```bash
python src/experiments/run_math500.py
```

### API Call
```bash
curl -X POST http://localhost:8100/a2a/run \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Solve x^2 - 5x + 6 = 0",
    "model_name": "claude",
    "dataset": "math500"
  }'
```

## Experiment Design

### Comparison Groups

1. **Baseline: Direct (No CoT)**
   - Single LLM call
   - No reasoning steps
   - Minimal tokens

2. **Baseline: CoT**
   - Single LLM call with "Let's think step by step"
   - Full reasoning chain
   - More tokens

3. **Proposed: A2A**
   - Planner + Solver (2 calls)
   - Structured reasoning
   - Token efficient

### Metrics

- **Accuracy**: Correct answers / Total problems
- **Token Usage**: Average tokens per problem
- **Token Efficiency**: Accuracy / (Tokens / 1000)
- **Cost**: Total cost in USD
- **Latency**: Average response time

## Expected Results

```
Method    | Accuracy | Avg Tokens | Efficiency | Cost (500 problems)
----------|----------|------------|------------|--------------------
Direct    |   ~45%   |    150     |   0.300    |     $0.50
CoT       |   ~65%   |   1200     |   0.054    |     $4.00
A2A       |   ~62%   |    500     |   0.124    |     $1.67
```

**Hypothesis**: A2A achieves similar accuracy to CoT with 50-60% fewer tokens.

## Files

- `src/a2a_adk/agents/planner.py` - Planner agent
- `src/a2a_adk/agents/solvers.py` - Solver agent
- `src/a2a_adk/agents/orchestrator.py` - Controller
- `src/a2a_adk/server/app.py` - FastAPI server
- `src/experiments/run_math500.py` - Full experiment
- `test_a2a_system.py` - Quick test

## Environment Variables

Required in `.env`:
```
OPENROUTER_API_KEY_A2A_PLAN_CLAUDE=sk-or-v1-...
OPENROUTER_API_KEY_A2A_SOLVER_CLAUDE=sk-or-v1-...
OPENROUTER_API_KEY_A2A_PLAN_GPT=sk-or-v1-...
OPENROUTER_API_KEY_A2A_SOLVER_GPT=sk-or-v1-...
OPENROUTER_API_KEY_COT_CLAUDE=sk-or-v1-...
OPENROUTER_API_KEY_COT_GPT=sk-or-v1-...
OPENROUTER_API_KEY_NO_COT_CLAUDE=sk-or-v1-...
OPENROUTER_API_KEY_NO_COT_GPT=sk-or-v1-...
```
