import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("Environment Setup Check")
print("="*60)

keys_to_check = [
    "OPENROUTER_API_KEY_A2A_PLAN_CLAUDE",
    "OPENROUTER_API_KEY_A2A_SOLVER_CLAUDE",
    "OPENROUTER_API_KEY_A2A_PLAN_GPT",
    "OPENROUTER_API_KEY_A2A_SOLVER_GPT",
    "OPENROUTER_API_KEY_COT_GPT",
    "OPENROUTER_API_KEY_COT_CLAUDE",
    "OPENROUTER_API_KEY_NO_COT_GPT",
    "OPENROUTER_API_KEY_NO_COT_CLAUDE"
]

all_set = True
for key in keys_to_check:
    value = os.getenv(key)
    if value:
        print(f"✓ {key}: {'*' * 10}")
    else:
        print(f"✗ {key}: NOT SET")
        all_set = False

print("="*60)
if all_set:
    print("✓ All API keys are configured!")
else:
    print("✗ Some API keys are missing. Please check .env file")

print("\nTesting imports...")
try:
    import httpx
    print("✓ httpx")
except ImportError as e:
    print(f"✗ httpx: {e}")

try:
    import fastapi
    print("✓ fastapi")
except ImportError as e:
    print(f"✗ fastapi: {e}")

try:
    from datasets import load_dataset
    print("✓ datasets")
except ImportError as e:
    print(f"✗ datasets: {e}")

try:
    import pandas
    print("✓ pandas")
except ImportError as e:
    print(f"✗ pandas: {e}")

print("="*60)
print("Setup check complete!")
print("="*60)
