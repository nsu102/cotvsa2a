import json
import os
from datetime import datetime
from typing import List, Dict
import pandas as pd

class Evaluator:
    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name
        self.results = []

    def add_result(
        self,
        sample_id: str,
        method: str,
        model: str,
        predicted: str,
        ground_truth: str,
        tokens: int,
        prompt_tokens: int,
        completion_tokens: int,
        is_correct: bool
    ):
        self.results.append({
            "sample_id": sample_id,
            "method": method,
            "model": model,
            "predicted": predicted,
            "ground_truth": ground_truth,
            "tokens": tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "is_correct": is_correct
        })

    def calculate_metrics(self) -> Dict:
        if not self.results:
            return {}

        df = pd.DataFrame(self.results)

        metrics = {}
        for method in df["method"].unique():
            for model in df["model"].unique():
                subset = df[(df["method"] == method) & (df["model"] == model)]

                if len(subset) == 0:
                    continue

                key = f"{method}_{model}"

                accuracy = subset["is_correct"].mean()
                total_tokens = subset["tokens"].sum()
                avg_tokens = subset["tokens"].mean()
                prompt_tokens = subset["prompt_tokens"].sum()
                completion_tokens = subset["completion_tokens"].sum()

                efficiency = (accuracy / (avg_tokens / 1000)) if avg_tokens > 0 else 0

                metrics[key] = {
                    "method": method,
                    "model": model,
                    "accuracy": accuracy,
                    "total_samples": len(subset),
                    "correct_samples": subset["is_correct"].sum(),
                    "total_tokens": int(total_tokens),
                    "avg_tokens_per_sample": float(avg_tokens),
                    "prompt_tokens": int(prompt_tokens),
                    "completion_tokens": int(completion_tokens),
                    "efficiency": float(efficiency)
                }

        return metrics

    def save_results(self, output_dir: str = "results"):
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{self.dataset_name}_{timestamp}"

        raw_file = os.path.join(output_dir, f"{base_filename}_raw.json")
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        metrics = self.calculate_metrics()
        metrics_file = os.path.join(output_dir, f"{base_filename}_metrics.json")
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)

        df = pd.DataFrame(self.results)
        csv_file = os.path.join(output_dir, f"{base_filename}_results.csv")
        df.to_csv(csv_file, index=False, encoding="utf-8")

        summary_file = os.path.join(output_dir, f"{base_filename}_summary.txt")
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"Dataset: {self.dataset_name}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Total Samples: {len(self.results)}\n\n")

            f.write("="*80 + "\n")
            f.write("METRICS SUMMARY\n")
            f.write("="*80 + "\n\n")

            for key, metric in sorted(metrics.items()):
                f.write(f"{key}:\n")
                f.write(f"  Accuracy: {metric['accuracy']:.4f} ({metric['correct_samples']}/{metric['total_samples']})\n")
                f.write(f"  Total Tokens: {metric['total_tokens']:,}\n")
                f.write(f"  Avg Tokens/Sample: {metric['avg_tokens_per_sample']:.2f}\n")
                f.write(f"  Prompt Tokens: {metric['prompt_tokens']:,}\n")
                f.write(f"  Completion Tokens: {metric['completion_tokens']:,}\n")
                f.write(f"  Efficiency (Acc per 1K tokens): {metric['efficiency']:.6f}\n")
                f.write("\n")

        print(f"\nResults saved to {output_dir}/")
        print(f"  - Raw results: {raw_file}")
        print(f"  - Metrics: {metrics_file}")
        print(f"  - CSV: {csv_file}")
        print(f"  - Summary: {summary_file}")

        return metrics

def compare_answers(predicted: str, ground_truth: str, dataset_type: str) -> bool:
    import re

    pred_clean = predicted.strip().lower()
    truth_clean = ground_truth.strip().lower()

    pred_clean = re.sub(r'\\boxed\{([^}]+)\}', r'\1', pred_clean)
    truth_clean = re.sub(r'\\boxed\{([^}]+)\}', r'\1', truth_clean)
    pred_clean = re.sub(r'\$+', '', pred_clean)
    truth_clean = re.sub(r'\$+', '', truth_clean)

    if ' or ' in pred_clean:
        pred_clean = pred_clean.split(' or ')[0].strip()

    pred_clean = pred_clean.strip()
    truth_clean = truth_clean.strip()

    pred_normalized = re.sub(r'\s+', '', pred_clean)
    truth_normalized = re.sub(r'\s+', '', truth_clean)

    if pred_normalized == truth_normalized:
        return True

    if dataset_type in ["gsm8k", "math500_algebra"]:
        pred_numbers = re.findall(r'-?\d+(?:\.\d+)?', pred_normalized)
        truth_numbers = re.findall(r'-?\d+(?:\.\d+)?', truth_normalized)

        if pred_numbers and truth_numbers:
            try:
                pred_val = float(pred_numbers[-1])
                truth_val = float(truth_numbers[0])
                return abs(pred_val - truth_val) < 0.01
            except:
                pass

    return truth_normalized in pred_normalized
