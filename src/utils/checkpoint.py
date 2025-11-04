import json
import os
from typing import Dict, Any, List

class CheckpointManager:
    def __init__(self, experiment_name: str, checkpoint_dir: str = "checkpoints"):
        self.experiment_name = experiment_name
        self.checkpoint_dir = os.path.join(checkpoint_dir, experiment_name)
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def get_checkpoint_path(self, method: str, model: str) -> str:
        return os.path.join(self.checkpoint_dir, f"{method}_{model}_ckpt.json")

    def save_checkpoint(self, method: str, model: str, results: List[Dict[str, Any]]):
        checkpoint_path = self.get_checkpoint_path(method, model)
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump({
                "method": method,
                "model": model,
                "completed": len(results),
                "results": results
            }, f, indent=2, ensure_ascii=False)
        print(f"💾 Checkpoint saved: {method}_{model} ({len(results)} samples)")

    def load_checkpoint(self, method: str, model: str) -> List[Dict[str, Any]]:
        checkpoint_path = self.get_checkpoint_path(method, model)
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📂 Loaded checkpoint: {method}_{model} ({data['completed']} samples)")
                return data['results']
        return []

    def has_checkpoint(self, method: str, model: str) -> bool:
        return os.path.exists(self.get_checkpoint_path(method, model))

    def get_completed_count(self, method: str, model: str) -> int:
        checkpoint = self.load_checkpoint(method, model)
        return len(checkpoint)

    def clear_checkpoint(self, method: str, model: str):
        checkpoint_path = self.get_checkpoint_path(method, model)
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            print(f"🗑️  Cleared checkpoint: {method}_{model}")
