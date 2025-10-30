import os
import sys
import httpx
from tqdm import tqdm
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.dataset_loader import DatasetLoader
from utils.evaluator import Evaluator, compare_answers
from utils.a2a_visualizer import A2AVisualizer
from baseline.cot_baseline import CoTBaseline
import json

load_dotenv()

def run_a2a_experiment(samples, model_name: str, evaluator: Evaluator):
    print(f"\nRunning A2A experiment with {model_name}...")

    client = httpx.Client(timeout=120.0)
    all_cards = []

    for sample in tqdm(samples, desc=f"A2A-{model_name}"):
        try:
            response = client.post(
                "http://localhost:8100/a2a/run",
                json={
                    "question": sample["question"],
                    "context": None,
                    "model_name": model_name,
                    "dataset": "gsm8k"
                }
            )
            response.raise_for_status()
            result = response.json()

            predicted = DatasetLoader.extract_answer_from_response(
                result["answer"], "gsm8k"
            )
            ground_truth = sample["answer"]

            is_correct = compare_answers(predicted, ground_truth, "gsm8k")

            if "cards" in result and result["cards"]:
                all_cards.extend(result["cards"])

            evaluator.add_result(
                sample_id=sample["id"],
                method="a2a",
                model=model_name,
                predicted=predicted,
                ground_truth=ground_truth,
                tokens=result["total_tokens"],
                prompt_tokens=result["prompt_tokens"],
                completion_tokens=result["completion_tokens"],
                is_correct=is_correct
            )

        except Exception as e:
            print(f"\nError processing {sample['id']}: {e}")
            evaluator.add_result(
                sample_id=sample["id"],
                method="a2a",
                model=model_name,
                predicted="ERROR",
                ground_truth=sample["answer"],
                tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                is_correct=False
            )

    if all_cards:
        os.makedirs("results", exist_ok=True)
        cards_file = f"results/gsm8k_a2a_{model_name}_cards.json"
        with open(cards_file, "w", encoding="utf-8") as f:
            json.dump(all_cards, f, indent=2, ensure_ascii=False)
        print(f"\nA2A cards saved to {cards_file}")

        flow_diagram = A2AVisualizer.generate_flow_diagram(all_cards[:50])
        print(flow_diagram)

    client.close()

def run_baseline_experiment(samples, model_name: str, use_cot: bool, evaluator: Evaluator):
    method_name = "cot" if use_cot else "no_cot"
    print(f"\nRunning {method_name.upper()} baseline with {model_name}...")

    baseline = CoTBaseline(model_name, "gsm8k", use_cot=use_cot)

    for sample in tqdm(samples, desc=f"{method_name.upper()}-{model_name}"):
        try:
            result = baseline.run(sample["question"])

            predicted = DatasetLoader.extract_answer_from_response(
                result["answer"], "gsm8k"
            )
            ground_truth = sample["answer"]

            is_correct = compare_answers(predicted, ground_truth, "gsm8k")

            evaluator.add_result(
                sample_id=sample["id"],
                method=method_name,
                model=model_name,
                predicted=predicted,
                ground_truth=ground_truth,
                tokens=result["total_tokens"],
                prompt_tokens=result["prompt_tokens"],
                completion_tokens=result["completion_tokens"],
                is_correct=is_correct
            )

        except Exception as e:
            print(f"\nError processing {sample['id']}: {e}")
            evaluator.add_result(
                sample_id=sample["id"],
                method=method_name,
                model=model_name,
                predicted="ERROR",
                ground_truth=sample["answer"],
                tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                is_correct=False
            )

    baseline.close()

def main():
    print("="*80)
    print("GSM8K Experiment")
    print("="*80)

    print("\nLoading GSM8K dataset (200 samples)...")
    samples = DatasetLoader.load_gsm8k(num_samples=200)
    print(f"Loaded {len(samples)} samples")

    evaluator = Evaluator("gsm8k")

    models = ["claude", "gpt"]

    for model in models:
        run_baseline_experiment(samples, model, use_cot=False, evaluator=evaluator)

    for model in models:
        run_baseline_experiment(samples, model, use_cot=True, evaluator=evaluator)

    print("\n" + "="*80)
    print("Starting A2A experiments (make sure server is running on port 8100)")
    print("="*80)

    for model in models:
        run_a2a_experiment(samples, model, evaluator=evaluator)

    print("\n" + "="*80)
    print("Calculating metrics and saving results...")
    print("="*80)

    metrics = evaluator.save_results("results")

    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    for key, metric in sorted(metrics.items()):
        print(f"\n{key}:")
        print(f"  Accuracy: {metric['accuracy']:.4f}")
        print(f"  Avg Tokens: {metric['avg_tokens_per_sample']:.2f}")
        print(f"  Efficiency: {metric['efficiency']:.6f}")

    print("\n" + "="*80)
    print("Experiment completed!")
    print("="*80)

if __name__ == "__main__":
    main()
