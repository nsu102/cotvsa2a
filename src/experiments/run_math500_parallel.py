import os
import sys
import httpx
import json
import threading
from tqdm import tqdm
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.dataset_loader import DatasetLoader
from utils.evaluator import Evaluator, compare_answers
from utils.a2a_visualizer import A2AVisualizer
from baseline.cot_baseline import CoTBaseline

load_dotenv()

CHECKPOINT_DIR = "checkpoints"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

checkpoint_lock = threading.Lock()

def save_checkpoint(checkpoint_name: str, data: dict):
    with checkpoint_lock:
        checkpoint_path = os.path.join(CHECKPOINT_DIR, f"{checkpoint_name}_ckpt.json")
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n[CKPT] Saved {checkpoint_name}")

def load_checkpoint(checkpoint_name: str):
    checkpoint_path = os.path.join(CHECKPOINT_DIR, f"{checkpoint_name}_ckpt.json")
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[CKPT] Loaded {checkpoint_name}")
        return data
    return None

def process_a2a_sample(sample, model_name: str, dataset: str):
    client = httpx.Client(timeout=180.0)
    try:
        response = client.post(
            "http://localhost:8100/a2a/run",
            json={
                "question": sample["question"],
                "context": None,
                "model_name": model_name,
                "dataset": dataset
            }
        )
        response.raise_for_status()
        result = response.json()

        raw_response = result["answer"]
        predicted = DatasetLoader.extract_answer_from_response(raw_response, dataset)
        ground_truth = sample["answer"]
        is_correct = compare_answers(predicted, ground_truth, dataset)

        cards = result.get("cards", [])

        return {
            "sample_id": sample["id"],
            "method": "a2a",
            "model": model_name,
            "predicted": predicted,
            "ground_truth": ground_truth,
            "raw_response": raw_response,
            "tokens": result["total_tokens"],
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
            "is_correct": is_correct,
            "cards": cards
        }

    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            error_msg = f"{error_msg}\nServer response: {e.response.text}"
        print(f"\n[ERROR] A2A {sample['id']}: {error_msg}")
        return {
            "sample_id": sample["id"],
            "method": "a2a",
            "model": model_name,
            "predicted": "ERROR",
            "ground_truth": sample["answer"],
            "raw_response": f"ERROR: {error_msg}",
            "tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "is_correct": False,
            "cards": []
        }
    finally:
        client.close()

def process_baseline_sample(sample, model_name: str, dataset: str, use_cot: bool):
    baseline = CoTBaseline(model_name, dataset, use_cot=use_cot)
    method_name = "cot" if use_cot else "no_cot"

    try:
        result = baseline.run(sample["question"])

        raw_response = result["answer"]
        predicted = DatasetLoader.extract_answer_from_response(raw_response, dataset)
        ground_truth = sample["answer"]
        is_correct = compare_answers(predicted, ground_truth, dataset)

        return {
            "sample_id": sample["id"],
            "method": method_name,
            "model": model_name,
            "predicted": predicted,
            "ground_truth": ground_truth,
            "raw_response": raw_response,
            "tokens": result["total_tokens"],
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
            "is_correct": is_correct
        }

    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"\n[ERROR] {method_name.upper()} {sample['id']}: {error_msg}")
        return {
            "sample_id": sample["id"],
            "method": method_name,
            "model": model_name,
            "predicted": "ERROR",
            "ground_truth": sample["answer"],
            "raw_response": f"ERROR: {error_msg}",
            "tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "is_correct": False
        }
    finally:
        baseline.close()

def run_a2a_experiment_parallel(samples, model_name: str, evaluator: Evaluator, max_workers: int = 10):
    checkpoint_name = f"math500_a2a_{model_name}"
    checkpoint_data = load_checkpoint(checkpoint_name)

    completed_ids = set()
    all_cards = []

    if checkpoint_data:
        for result in checkpoint_data["results"]:
            evaluator.add_result(**{k: v for k, v in result.items() if k not in ["cards", "raw_response"]})
            all_cards.extend(result.get("cards", []))
            completed_ids.add(result["sample_id"])
        print(f"[RESUME] A2A-{model_name}: {len(completed_ids)}/{len(samples)} completed")

    remaining_samples = [s for s in samples if s["id"] not in completed_ids]

    if not remaining_samples:
        print(f"[SKIP] A2A-{model_name} already complete")
        return all_cards

    print(f"\nRunning A2A experiment with {model_name} ({len(remaining_samples)} remaining)...")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_a2a_sample, sample, model_name, "math500_algebra"): sample
            for sample in remaining_samples
        }

        with tqdm(total=len(remaining_samples), desc=f"A2A-{model_name}") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                evaluator.add_result(**{k: v for k, v in result.items() if k not in ["cards", "raw_response"]})
                all_cards.extend(result.get("cards", []))

                pbar.update(1)

                if len(results) % 10 == 0:
                    save_checkpoint(checkpoint_name, {"results": results})

    save_checkpoint(checkpoint_name, {"results": results})

    if all_cards:
        os.makedirs("results", exist_ok=True)
        cards_file = f"results/math500_a2a_{model_name}_cards.json"
        with open(cards_file, "w", encoding="utf-8") as f:
            json.dump(all_cards, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] A2A cards: {cards_file}")

    return all_cards

def run_baseline_experiment_parallel(samples, model_name: str, use_cot: bool, evaluator: Evaluator, max_workers: int = 10):
    method_name = "cot" if use_cot else "no_cot"
    checkpoint_name = f"math500_{method_name}_{model_name}"
    checkpoint_data = load_checkpoint(checkpoint_name)

    completed_ids = set()

    if checkpoint_data:
        for result in checkpoint_data["results"]:
            evaluator.add_result(**{k: v for k, v in result.items() if k != "raw_response"})
            completed_ids.add(result["sample_id"])
        print(f"[RESUME] {method_name.upper()}-{model_name}: {len(completed_ids)}/{len(samples)} completed")

    remaining_samples = [s for s in samples if s["id"] not in completed_ids]

    if not remaining_samples:
        print(f"[SKIP] {method_name.upper()}-{model_name} already complete")
        return

    print(f"\nRunning {method_name.upper()} baseline with {model_name} ({len(remaining_samples)} remaining)...")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_baseline_sample, sample, model_name, "math500_algebra", use_cot): sample
            for sample in remaining_samples
        }

        with tqdm(total=len(remaining_samples), desc=f"{method_name.upper()}-{model_name}") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                evaluator.add_result(**{k: v for k, v in result.items() if k != "raw_response"})

                pbar.update(1)

                if len(results) % 10 == 0:
                    save_checkpoint(checkpoint_name, {"results": results})

    save_checkpoint(checkpoint_name, {"results": results})

def main():
    print("="*80)
    print("MATH-500 Algebra Experiment (Parallel Execution)")
    print("="*80)

    print("\nLoading MATH-500 Algebra dataset (124 samples)...")
    samples = DatasetLoader.load_math500_algebra(num_samples=124)
    print(f"Loaded {len(samples)} samples")

    evaluator = Evaluator("math500_algebra")

    models = ["claude", "gpt"]

    for model in models:
        run_baseline_experiment_parallel(samples, model, use_cot=False, evaluator=evaluator, max_workers=15)

    for model in models:
        run_baseline_experiment_parallel(samples, model, use_cot=True, evaluator=evaluator, max_workers=15)

    print("\n" + "="*80)
    print("Starting A2A experiments (make sure server is running on port 8100)")
    print("="*80)

    for model in models:
        run_a2a_experiment_parallel(samples, model, evaluator=evaluator, max_workers=10)

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
