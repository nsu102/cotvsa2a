from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

@dataclass
class A2ACard:
    sender: str
    recipient: str
    message_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict) -> 'A2ACard':
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'A2ACard':
        return cls.from_dict(json.loads(json_str))

class TaskCard:
    @staticmethod
    def create(sender: str, recipient: str, task_description: str, context: Optional[Dict] = None):
        return A2ACard(
            sender=sender,
            recipient=recipient,
            message_type="task",
            content=task_description,
            metadata={"context": context} if context else None
        )

class ResultCard:
    @staticmethod
    def create(sender: str, recipient: str, result: str, status: str = "success", metadata: Optional[Dict] = None):
        meta = {"status": status}
        if metadata:
            meta.update(metadata)
        return A2ACard(
            sender=sender,
            recipient=recipient,
            message_type="result",
            content=result,
            metadata=meta
        )

class QueryCard:
    @staticmethod
    def create(sender: str, recipient: str, query: str, options: Optional[List[str]] = None):
        return A2ACard(
            sender=sender,
            recipient=recipient,
            message_type="query",
            content=query,
            metadata={"options": options} if options else None
        )

class ControlCard:
    @staticmethod
    def create(sender: str, recipient: str, action: str, parameters: Optional[Dict] = None):
        return A2ACard(
            sender=sender,
            recipient=recipient,
            message_type="control",
            content=action,
            metadata={"parameters": parameters} if parameters else None
        )

class A2ACardProtocol:
    PLANNER = "planner"
    SOLVER = "solver"
    CONTROLLER = "controller"

    @staticmethod
    def create_task_card(from_agent: str, to_agent: str, task: str, context: Optional[Dict] = None) -> A2ACard:
        return TaskCard.create(from_agent, to_agent, task, context)

    @staticmethod
    def create_result_card(from_agent: str, to_agent: str, result: str, status: str = "success", metadata: Optional[Dict] = None) -> A2ACard:
        return ResultCard.create(from_agent, to_agent, result, status, metadata)

    @staticmethod
    def create_query_card(from_agent: str, to_agent: str, query: str, options: Optional[List[str]] = None) -> A2ACard:
        return QueryCard.create(from_agent, to_agent, query, options)

    @staticmethod
    def create_control_card(from_agent: str, to_agent: str, action: str, parameters: Optional[Dict] = None) -> A2ACard:
        return ControlCard.create(from_agent, to_agent, action, parameters)
