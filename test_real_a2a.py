import subprocess
import time
import httpx
import json

print("Testing Real A2A Protocol with ADK")
print("="*80)

solver_process = subprocess.Popen(
    ["python", "-m", "src.a2a_adk.solver_agent", "gpt", "gsm8k", "8002"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

print("Started Solver Agent on port 8002")
time.sleep(3)

planner_process = subprocess.Popen(
    ["python", "-m", "src.a2a_adk.planner_agent", "gpt", "gsm8k", "http://localhost:8002", "8001"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

print("Started Planner Agent on port 8001")
time.sleep(3)

try:
    print("\n" + "="*80)
    print("Checking Agent Cards...")
    print("="*80)

    client = httpx.Client(timeout=10.0)

    solver_card_response = client.get("http://localhost:8002/.well-known/agent-card.json")
    print(f"\nSolver Agent Card (port 8002):")
    print(json.dumps(solver_card_response.json(), indent=2))

    planner_card_response = client.get("http://localhost:8001/.well-known/agent-card.json")
    print(f"\nPlanner Agent Card (port 8001):")
    print(json.dumps(planner_card_response.json(), indent=2))

    print("\n" + "="*80)
    print("Testing Planner Agent...")
    print("="*80)

    test_question = "What is 25 * 17?"

    print(f"\nSending question: {test_question}")

    response = client.post(
        "http://localhost:8001/invoke",
        json={"input": test_question},
        timeout=60.0
    )

    result = response.json()

    print(f"\nResponse:")
    print(json.dumps(result, indent=2))

    print("\n" + "="*80)
    print("✅ Real A2A Protocol Test Complete!")
    print("="*80)

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\nCleaning up...")
    planner_process.terminate()
    solver_process.terminate()
    planner_process.wait()
    solver_process.wait()
    client.close()
    print("Agents stopped")
