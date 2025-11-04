import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

from src.a2a_adk.agents.orchestrator import orchestrator_agent, init_runtime
from src.a2a_adk.agents.planner import planner_agent
from src.a2a_adk.agents.solvers import solver_agent

def test_a2a_system():
    print("="*80)
    print("Testing A2A Math Solver System")
    print("="*80)

    runtime = init_runtime()
    runtime.register("planner_agent", planner_agent)
    runtime.register("solver_agent", solver_agent)

    test_problems = [
        "What is 15 + 27?",
        "If a shirt costs $12 and you buy 3 shirts, how much do you pay?",
        "Solve for x: 2x + 5 = 13"
    ]

    for i, problem in enumerate(test_problems, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {problem}")
        print(f"{'='*80}")

        try:
            result = orchestrator_agent(
                problem=problem,
                model="claude",
                dataset="math500"
            )

            print(f"\nFinal Answer: {result['final_answer']}")
            print(f"Total Tokens: {result['total_tokens']}")
            print(f"  - Input: {result['prompt_tokens']}")
            print(f"  - Output: {result['completion_tokens']}")
            print(f"Cards Generated: {len(result['cards'])}")

            print("\nAgent Communication Flow:")
            for j, card in enumerate(result['cards'], 1):
                print(f"  {j}. {card['sender']} → {card['recipient']}: {card['message_type']}")

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("Testing completed!")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_a2a_system()
