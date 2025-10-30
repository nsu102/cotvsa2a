# A2A Card Protocol Specification

## 개요

A2A (Agent-to-Agent) 카드는 에이전트 간 통신을 위한 표준화된 메시지 포맷입니다. 이 프로토콜은 멀티 에이전트 시스템에서 구조화되고 추적 가능한 통신을 가능하게 합니다.

## 카드 구조

### 기본 A2ACard

```python
{
  "sender": "planner",           # 발신자 에이전트 ID
  "recipient": "solver",          # 수신자 에이전트 ID
  "message_type": "task",         # 메시지 유형
  "content": "문제를 풀어주세요",   # 메시지 내용
  "metadata": {...},              # 추가 메타데이터
  "timestamp": "2025-01-15T10:30:00"  # ISO 8601 타임스탬프
}
```

## 카드 유형

### 1. TaskCard (작업 요청)

**용도**: 한 에이전트가 다른 에이전트에게 작업을 요청할 때 사용

```python
{
  "sender": "controller",
  "recipient": "planner",
  "message_type": "task",
  "content": "What is 25 * 17?",
  "metadata": {
    "dataset": "gsm8k",
    "context": {...}
  },
  "timestamp": "2025-01-15T10:30:00"
}
```

**사용 예**:
- Controller → Planner: 초기 문제 제시
- Planner → Solver: 하위 작업 위임

### 2. ResultCard (결과 반환)

**용도**: 작업 완료 후 결과를 반환할 때 사용

```python
{
  "sender": "solver",
  "recipient": "planner",
  "message_type": "result",
  "content": "425",
  "metadata": {
    "status": "success",
    "turn": 1,
    "tokens": 120
  },
  "timestamp": "2025-01-15T10:30:15"
}
```

**Status 값**:
- `success`: 작업 성공
- `completed`: 전체 프로세스 완료
- `error`: 에러 발생
- `partial`: 부분 완료

### 3. QueryCard (질의)

**용도**: 정보를 요청하거나 선택지를 제시할 때 사용

```python
{
  "sender": "planner",
  "recipient": "solver",
  "message_type": "query",
  "content": "어떤 방법을 사용할까요?",
  "metadata": {
    "options": ["방법A", "방법B", "방법C"]
  },
  "timestamp": "2025-01-15T10:30:10"
}
```

### 4. ControlCard (제어 명령)

**용도**: 시스템 제어나 메타 명령을 전달할 때 사용

```python
{
  "sender": "controller",
  "recipient": "planner",
  "message_type": "control",
  "content": "stop",
  "metadata": {
    "parameters": {"reason": "timeout"}
  },
  "timestamp": "2025-01-15T10:35:00"
}
```

## 에이전트 역할

### CONTROLLER
- **역할**: 전체 A2A 프로세스 조율
- **책임**: 초기 작업 할당, 최종 결과 수집, 타임아웃 관리
- **송신**: TaskCard, ControlCard
- **수신**: ResultCard

### PLANNER
- **역할**: 문제 분석 및 작업 계획
- **책임**: 문제 분해, Solver 호출 결정, 최종 답변 생성
- **송신**: TaskCard (→ Solver), ResultCard (→ Controller)
- **수신**: TaskCard (← Controller), ResultCard (← Solver)

### SOLVER
- **역할**: 구체적 작업 실행
- **책임**: 할당된 하위 작업 수행, 결과 계산
- **송신**: ResultCard (→ Planner)
- **수신**: TaskCard (← Planner)

## 통신 흐름 예시

### GSM8K 수학 문제 해결 (3턴)

```
1. CONTROLLER → [TASK] → PLANNER
   Task: "Janet's ducks lay 16 eggs per day..."

2. PLANNER → [TASK] → SOLVER (강제 첫 호출)
   Subtask: "Calculate 16 eggs - 3 eaten - 4 muffins"

3. SOLVER → [RESULT] → PLANNER
   Result: "9"

4. PLANNER → [TASK] → SOLVER (체이닝)
   Subtask: "Calculate daily income: 9 eggs * $2"

5. SOLVER → [RESULT] → PLANNER
   Result: "$18"

6. PLANNER → [RESULT] → CONTROLLER
   Final Answer: "18"
```

### HotpotQA 멀티홉 QA (5턴)

```
1. CONTROLLER → [TASK] → PLANNER
   Task: "What is the birthplace of the director of Inception?"

2. PLANNER → [TASK] → SOLVER (강제 첫 호출)
   Subtask: "Find who directed the movie Inception"

3. SOLVER → [RESULT] → PLANNER
   Result: "Christopher Nolan"

4. PLANNER → [TASK] → SOLVER (체이닝 - 2nd hop)
   Subtask: "Find Christopher Nolan's birthplace"

5. SOLVER → [RESULT] → PLANNER
   Result: "Westminster, London, England"

6. PLANNER → [RESULT] → CONTROLLER
   Final Answer: "Westminster, London, England"
```

**핵심 패턴**:
- 첫 턴: 강제 Solver 호출
- 중간 턴: 체이닝 (Planner가 여러 번 Solver 호출 가능)
- Solver: 최소 정보만 반환 (1문장, 토큰 절약)
- 데이터셋별 턴 수: GSM8K(3), HotpotQA(5)

### Flow Diagram
```
1. CONTROLLER    → [TASK]    PLANNER
2. PLANNER       → [TASK]    SOLVER
3. SOLVER        ← [RESULT]  PLANNER
4. PLANNER       → [TASK]    SOLVER
5. SOLVER        ← [RESULT]  PLANNER
6. PLANNER       ← [RESULT]  CONTROLLER
```

## 구현

### Python 사용 예

```python
from shared.a2a_card import A2ACardProtocol

# TaskCard 생성
task_card = A2ACardProtocol.create_task_card(
    from_agent=A2ACardProtocol.CONTROLLER,
    to_agent=A2ACardProtocol.PLANNER,
    task="Solve this problem",
    context={"dataset": "gsm8k"}
)

# ResultCard 생성
result_card = A2ACardProtocol.create_result_card(
    from_agent=A2ACardProtocol.SOLVER,
    to_agent=A2ACardProtocol.PLANNER,
    result="42",
    status="success",
    metadata={"tokens": 150}
)

# JSON 변환
task_json = task_card.to_json()
result_dict = result_card.to_dict()
```

## 카드 시각화

### A2AVisualizer 사용

```python
from utils.a2a_visualizer import A2AVisualizer

# 카드 시각화
visualization = A2AVisualizer.visualize_cards(cards)
print(visualization)

# Flow diagram 생성
flow = A2AVisualizer.generate_flow_diagram(cards)
print(flow)

# 파일 저장
A2AVisualizer.save_card_visualization(cards, "results/cards.txt")
```

### 실험에서 카드 추적

실험 실행 시 A2A 카드는 자동으로 수집되고 저장됩니다:

```bash
python src/experiments/run_gsm8k.py
# → results/gsm8k_a2a_claude_cards.json
# → results/gsm8k_a2a_gpt_cards.json

python src/experiments/run_hotpotqa.py
# → results/hotpotqa_a2a_claude_cards.json
# → results/hotpotqa_a2a_gpt_cards.json
```

## 디버깅 및 분석

### 카드 로그 검사

```python
import json

# 카드 파일 로드
with open("results/gsm8k_a2a_claude_cards.json") as f:
    cards = json.load(f)

# 카드 타입별 통계
from collections import Counter
card_types = Counter(card["message_type"] for card in cards)
print(card_types)
# Output: {'task': 120, 'result': 120}

# 평균 턴 수 계산
planner_to_solver = sum(1 for c in cards if c["sender"] == "planner" and c["recipient"] == "solver")
avg_turns = planner_to_solver / 200  # 200 samples
print(f"Average turns per problem: {avg_turns:.2f}")
```

### 성능 분석

```python
# 성공/실패 비율
success_cards = [c for c in cards if c.get("metadata", {}).get("status") == "success"]
completion_cards = [c for c in cards if c.get("metadata", {}).get("status") == "completed"]

print(f"Solver success rate: {len(success_cards) / len([c for c in cards if c['message_type'] == 'result']):.2%}")
print(f"Overall completion rate: {len(completion_cards) / 200:.2%}")
```

## 확장성

### 새로운 카드 타입 추가

```python
@dataclass
class ErrorCard(A2ACard):
    message_type: str = "error"

    @classmethod
    def create(cls, sender: str, recipient: str, error_msg: str, error_type: str):
        return cls(
            sender=sender,
            recipient=recipient,
            message_type="error",
            content=error_msg,
            metadata={"error_type": error_type}
        )
```

### 새로운 에이전트 추가

```python
# A2ACardProtocol 확장
class ExtendedA2ACardProtocol(A2ACardProtocol):
    VALIDATOR = "validator"
    REVIEWER = "reviewer"
```

## 베스트 프랙티스

1. **명확한 Content**: 카드의 `content` 필드는 명확하고 구체적이어야 함
2. **풍부한 Metadata**: 디버깅과 분석을 위해 충분한 메타데이터 포함
3. **타임스탬프 활용**: 성능 분석과 병목 지점 식별에 활용
4. **Status 일관성**: ResultCard의 status 값을 일관되게 사용
5. **에러 처리**: 실패 케이스도 카드로 기록하여 추적성 확보

## 토큰 효율성과의 관계

A2A 카드 프로토콜은 토큰 효율성 향상에 기여합니다:

1. **명확한 경계**: 각 에이전트가 자신의 역할에만 집중
2. **컨텍스트 제한**: 전체 대화 이력 대신 필요한 정보만 전달
3. **조건부 실행**: Planner가 필요시에만 Solver 호출
4. **추적 가능성**: 어떤 단계에서 토큰이 사용되었는지 정확히 파악

## 결론

A2A 카드 프로토콜은 멀티 에이전트 시스템에서:
- 구조화된 통신
- 명확한 책임 분리
- 완전한 추적성
- 효율적인 토큰 사용

을 가능하게 하여 CoT 대비 토큰 효율성을 유지하면서도 복잡한 추론 작업을 수행할 수 있게 합니다.
