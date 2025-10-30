import httpx
import json

print("Testing ADK A2A Server...")
print("="*80)

client = httpx.Client(timeout=60.0)

test_question = "What is 25 * 17?"

payload = {
    "question": test_question,
    "context": None,
    "model_name": "gpt",
    "dataset": "gsm8k"
}

print(f"\nSending request:")
print(f"Question: {test_question}")
print(f"Model: gpt")
print(f"Dataset: gsm8k")

try:
    response = client.post(
        "http://localhost:8100/a2a/run",
        json=payload
    )
    response.raise_for_status()

    result = response.json()

    print(f"\n{'='*80}")
    print("Response received:")
    print(f"{'='*80}")
    print(f"\nAnswer: {result['answer']}")
    print(f"\nTotal tokens: {result['total_tokens']}")
    print(f"  - Prompt: {result['prompt_tokens']}")
    print(f"  - Completion: {result['completion_tokens']}")

    print(f"\n{'='*80}")
    print("Execution steps:")
    print(f"{'='*80}")

    for step in result['steps']:
        print(f"\nTurn {step['turn']} - {step['agent'].upper()}")
        print(f"Content: {step['content'][:200]}...")
        print(f"Tokens: {step['tokens']}")

    print(f"\n{'='*80}")
    print("✅ Test successful!")
    print(f"{'='*80}")

except Exception as e:
    print(f"\n{'='*80}")
    print("❌ Test failed!")
    print(f"{'='*80}")
    print(f"Error: {e}")

finally:
    client.close()
