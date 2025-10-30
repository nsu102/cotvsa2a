from typing import List, Dict
import json

class A2AVisualizer:
    @staticmethod
    def visualize_cards(cards: List[Dict]) -> str:
        output = []
        output.append("=" * 80)
        output.append("A2A CARD COMMUNICATION FLOW")
        output.append("=" * 80)

        for i, card in enumerate(cards, 1):
            sender = card.get("sender", "unknown")
            recipient = card.get("recipient", "unknown")
            msg_type = card.get("message_type", "unknown")
            content = card.get("content", "")
            metadata = card.get("metadata", {})
            timestamp = card.get("timestamp", "")

            output.append(f"\n[Card {i}] {timestamp}")
            output.append(f"  From: {sender.upper()}")
            output.append(f"  To:   {recipient.upper()}")
            output.append(f"  Type: {msg_type.upper()}")

            if msg_type == "task":
                output.append(f"  Task: {content[:100]}...")
            elif msg_type == "result":
                status = metadata.get("status", "unknown")
                output.append(f"  Status: {status}")
                output.append(f"  Result: {content[:100]}...")
            elif msg_type == "control":
                output.append(f"  Action: {content}")
            else:
                output.append(f"  Content: {content[:100]}...")

            if metadata:
                output.append(f"  Metadata: {json.dumps(metadata, ensure_ascii=False)}")

            output.append("  " + "-" * 76)

        output.append("\n" + "=" * 80)
        output.append(f"Total Cards: {len(cards)}")
        output.append("=" * 80)

        return "\n".join(output)

    @staticmethod
    def save_card_visualization(cards: List[Dict], filepath: str):
        visualization = A2AVisualizer.visualize_cards(cards)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(visualization)

    @staticmethod
    def generate_flow_diagram(cards: List[Dict]) -> str:
        output = []
        output.append("\nA2A Communication Flow Diagram:")
        output.append("=" * 80)

        for i, card in enumerate(cards, 1):
            sender = card.get("sender", "?")
            recipient = card.get("recipient", "?")
            msg_type = card.get("message_type", "?")

            if msg_type == "task":
                symbol = "→ [TASK]"
            elif msg_type == "result":
                symbol = "← [RESULT]"
            elif msg_type == "control":
                symbol = "⚙ [CONTROL]"
            else:
                symbol = "• [MSG]"

            output.append(f"{i}. {sender.upper():12} {symbol:12} {recipient.upper()}")

        output.append("=" * 80)
        return "\n".join(output)
