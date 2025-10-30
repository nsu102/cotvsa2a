from datasets import load_dataset
import json

print("Loading HuggingFaceH4/MATH-500...")
print("="*80)

dataset = load_dataset("HuggingFaceH4/MATH-500", split="test")

print(f"Total samples: {len(dataset)}")
print(f"Features: {list(dataset.features.keys())}")

algebra_samples = [item for item in dataset if item.get('subject') == 'algebra' or item.get('type') == 'Algebra']

print(f"\nAlgebra samples: {len(algebra_samples)}")

if len(algebra_samples) > 0:
    print("\n" + "="*80)
    print("Sample 1:")
    print("="*80)
    print(json.dumps(algebra_samples[0], indent=2, ensure_ascii=False))

    print("\n" + "="*80)
    print("Sample 2:")
    print("="*80)
    print(json.dumps(algebra_samples[1], indent=2, ensure_ascii=False))

    print("\n" + "="*80)
    print("Sample 3:")
    print("="*80)
    print(json.dumps(algebra_samples[2], indent=2, ensure_ascii=False))

print("\n" + "="*80)
print("All subjects in dataset:")
print("="*80)
subjects = {}
for item in dataset:
    subject = item.get('subject') or item.get('type') or 'unknown'
    subjects[subject] = subjects.get(subject, 0) + 1

for subject, count in sorted(subjects.items(), key=lambda x: x[1], reverse=True):
    print(f"  {subject}: {count} samples")
