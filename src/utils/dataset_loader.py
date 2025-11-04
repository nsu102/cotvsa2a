from datasets import load_dataset
from typing import List, Dict
import re

class DatasetLoader:
    @staticmethod
    def load_2wikimultihopqa(num_samples: int = 100) -> List[Dict]:
        dataset = load_dataset("THUDM/2WikiMultihopQA", split="train")
        samples = []

        for i, item in enumerate(dataset):
            if i >= num_samples:
                break

            question = item["question"]
            answer = item["answer"]

            context_parts = []
            if "context" in item:
                for ctx in item["context"]:
                    if isinstance(ctx, list) and len(ctx) > 1:
                        context_parts.append(" ".join(ctx[1]))
            context = " ".join(context_parts) if context_parts else ""

            samples.append({
                "id": f"2wikimhqa_{i}",
                "question": question,
                "answer": answer,
                "context": context,
                "dataset": "2wikimultihopqa"
            })

        return samples

    @staticmethod
    def load_math500(num_samples: int = 500) -> List[Dict]:
        dataset = load_dataset("HuggingFaceH4/MATH-500", split="test")
        samples = []

        for i, item in enumerate(dataset):
            if i >= num_samples:
                break

            problem = item["problem"]
            answer = item["answer"]
            solution = item.get("solution", "")
            level = item.get("level", "unknown")
            subject = item.get("subject", "unknown")

            samples.append({
                "id": f"math500_{i}",
                "question": problem,
                "answer": answer,
                "solution": solution,
                "level": level,
                "subject": subject,
                "dataset": "math500"
            })

        return samples


    @staticmethod
    def _extract_answer_number(answer_text: str) -> str:
        matches = re.findall(r'####\s*(-?\d+(?:,\d{3})*(?:\.\d+)?)', answer_text)
        if matches:
            return matches[0].replace(',', '')

        matches = re.findall(r'(-?\d+(?:,\d{3})*(?:\.\d+)?)', answer_text)
        if matches:
            return matches[-1].replace(',', '')

        return answer_text.strip()

    @staticmethod
    def extract_answer_from_response(response: str, dataset_type: str) -> str:
        if not response or not response.strip():
            return ""

        response_lower = response.lower()

        if "answer:" in response_lower:
            answer_part = response.split("nswer:")[-1].strip()
            if dataset_type == "math500":
                answer_part = answer_part.split('\n')[0].strip()
                cleaned = DatasetLoader._clean_math_answer(answer_part)
                if cleaned:
                    return cleaned
            elif dataset_type == "2wikimultihopqa":
                lines = answer_part.split('\n')
                return lines[0].strip()
            else:
                lines = answer_part.split('\n')
                return lines[0].strip()

        if dataset_type == "math500":
            cleaned = DatasetLoader._clean_math_answer(response)
            if cleaned:
                return cleaned

            lines = response.strip().split('\n')
            for line in reversed(lines):
                cleaned = DatasetLoader._clean_math_answer(line)
                if cleaned and len(cleaned) > 0:
                    return cleaned

        lines = response.strip().split('\n')
        last_line = lines[-1].strip()
        if last_line:
            return last_line

        return response.strip()

    @staticmethod
    def _clean_math_answer(text: str) -> str:
        text = text.strip()

        text = re.sub(r'\\boxed\{([^}]+)\}', r'\1', text)
        text = re.sub(r'\$+', '', text)
        text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)

        if ' or ' in text:
            parts = text.split(' or ')
            text = parts[0].strip()

        text = re.sub(r'\s+', '', text)

        text = text.strip()
        return text
