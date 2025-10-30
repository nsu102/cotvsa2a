import httpx
import json
from dotenv import load_dotenv

load_dotenv()

print("="*80)
print("A2A Server Simple Test")
print("="*80)

client = httpx.Client(timeout=120.0)

test_question = "What is 5 + 3?"

print(f"\nTest Question: {test_question}")
print("\nSending request to A2A server...")

try:
    response = client.post(
        "http://localhost:8100/a2a/run",
        json={
            "question": test_question,
            "context": None,
            "model_name": "claude",
            "dataset": "gsm8k"
        }
    )

    response.raise_for_status()
    result = response.json()

    print("\n" + "="*80)
    print("RESPONSE")
    print("="*80)

    print(f"\nFinal Answer: {result['answer']}")
    print(f"\nToken Usage:")
    print(f"  Total: {result['total_tokens']}")
    print(f"  Prompt: {result['prompt_tokens']}")
    print(f"  Completion: {result['completion_tokens']}")

    print(f"\nSteps ({len(result['steps'])} steps):")
    for i, step in enumerate(result['steps'], 1):
        print(f"\n  Step {i} (Turn {step.get('turn', '?')}):")
        print(f"    Agent: {step['agent']}")
        print(f"    Tokens: {step['tokens']}")
        print(f"    Content: {step['content'][:100]}...")

    print(f"\nA2A Cards ({len(result['cards'])} cards):")
    for i, card in enumerate(result['cards'], 1):
        print(f"\n  Card {i}:")
        print(f"    {card['sender']} → {card['recipient']}")
        print(f"    Type: {card['message_type']}")
        print(f"    Content: {card['content'][:80]}...")

    print("\n" + "="*80)
    print("✅ A2A Server Test PASSED")
    print("="*80)

except httpx.ConnectError:
    print("\n❌ ERROR: Cannot connect to A2A server at http://localhost:8100")
    print("   Please start the server first: python src/a2a/server.py")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    if hasattr(e, 'response'):
        print(f"   Response: {e.response.text}")

client.close()
