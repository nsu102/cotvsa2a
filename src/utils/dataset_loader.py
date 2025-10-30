from datasets import load_dataset
from typing import List, Dict, Tuple
import re

class DatasetLoader:
    @staticmethod
    def load_math500_algebra(num_samples: int = 124) -> List[Dict]:
        dataset = load_dataset("HuggingFaceH4/MATH-500", split="test")
        samples = []

        algebra_items = [item for item in dataset if item.get('subject') == 'Algebra']

        for i, item in enumerate(algebra_items):
            if i >= num_samples:
                break

            problem = item["problem"]
            answer = item["answer"]
            solution = item.get("solution", "")
            level = item.get("level", "unknown")

            samples.append({
                "id": f"math500_algebra_{i}",
                "question": problem,
                "answer": answer,
                "solution": solution,
                "level": level,
                "dataset": "math500_algebra"
            })

        return samples
    @staticmethod
    def load_gsm8k(num_samples: int = 200) -> List[Dict]:
        dataset = load_dataset("openai/gsm8k", "main", split="test")
        samples = []

        for i, item in enumerate(dataset):
            if i >= num_samples:
                break

            question = item["question"]
            answer = item["answer"]

            answer_number = DatasetLoader._extract_answer_number(answer)

            samples.append({
                "id": f"gsm8k_{i}",
                "question": question,
                "answer": answer_number,
                "dataset": "gsm8k"
            })

        return samples

    @staticmethod
    def load_hotpotqa(num_samples: int = 100) -> List[Dict]:
        dataset = load_dataset("hotpot_qa", "distractor", split="validation")
        samples = []

        for i, item in enumerate(dataset):
            if i >= num_samples:
                break

            question = item["question"]
            answer = item["answer"]
            context = item["context"]

            context_text = DatasetLoader._format_hotpot_context(context)

            samples.append({
                "id": f"hotpotqa_{i}",
                "question": question,
                "context": context_text,
                "answer": answer,
                "dataset": "hotpotqa"
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
    def _format_hotpot_context(context: Dict) -> str:
        formatted = []
        titles = context.get("title", [])
        sentences = context.get("sentences", [])

        for title, sents in zip(titles, sentences):
            text = " ".join(sents)
            formatted.append(f"[{title}] {text}")

        return "\n\n".join(formatted)

    @staticmethod
    def extract_answer_from_response(response: str, dataset_type: str) -> str:
        if not response or not response.strip():
            return ""

        response_lower = response.lower()

        if "answer:" in response_lower:
            answer_part = response.split("nswer:")[-1].strip()
            if dataset_type == "gsm8k":
                matches = re.findall(r'(-?\d+(?:,\d{3})*(?:\.\d+)?)', answer_part)
                if matches:
                    return matches[0].replace(',', '')
            elif dataset_type == "math500_algebra":
                answer_part = answer_part.split('\n')[0].strip()
                cleaned = DatasetLoader._clean_math_answer(answer_part)
                if cleaned:
                    return cleaned
            else:
                lines = answer_part.split('\n')
                return lines[0].strip()

        if dataset_type == "gsm8k":
            matches = re.findall(r'(-?\d+(?:,\d{3})*(?:\.\d+)?)', response)
            if matches:
                return matches[-1].replace(',', '')

        if dataset_type == "math500_algebra":
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
