# Title
Comparing Monolithic Chain-of-Thought (CoT) Prompting with Agent-to-Agent (A2A) Protocol for Token-Efficient Reasoning

## 1. 목적 (Goal)
이 실험의 목적은 다음을 보이는 것이다:

1. **동일하거나 유사한 정답률**을 유지하면서도
2. **A2A(agent-to-agent) 프로토콜**이
3. **전통적인 단일 CoT 프롬프트보다 토큰 사용량(입력+출력)이 유의하게 적다**는 것을 수치로 증명

이를 위해 Google의 `python-a2a` 라이브러리와 `FastAPI`로 구성한 **로컬 A2A 서빙 환경**을 사용하고,  
**LLM 백엔드는 OpenRouter를 통해 `claude-haiku-4.5`와 `gpt-5o-mini` 두 모델을 모두 사용하여 교차 실험**을 수행한다.

---

## 2. 시스템 구조 개요

### 2.1 아키텍처
- **Client / Runner**: 실험 스크립트 (Jupyter / CLI / pytest 형식)
- **Local A2A Server (FastAPI)**:  
  - 엔드포인트: `POST /a2a/run`
  - 역할: 요청을 받아 planner-agent와 solver-agent를 순차/동시 호출
  - 내부에서 `python-a2a` 호출
  - 내부 LLM 호출부는 **OpenRouter REST API**로 통일
  - 요청 시 사용할 모델명을 전달받아 **동일 파이프라인에 서로 다른 LLM**을 꽂을 수 있게 함
- **LLM Backend (OpenRouter)**:
  - URL: `https://openrouter.ai/api/v1/chat/completions`
  - 헤더: `Authorization: Bearer $OPENROUTER_API_KEY`
  - **모델 두 개**:
    - M1: `anthropic/claude-haiku-4.5`
    - M2: `openai/gpt-5o-mini`
  - 모든 호출에서 `usage` 필드 파싱

### 2.2 비교 대상

1. **Baseline 1: Plain CoT**
   - 프롬프트: `{"role": "user", "content": "question ... Let's think step by step."}`
   - 한 번의 OpenRouter 호출로 전체 추론
   - **두 모델 모두 실행** → CoT(M1), CoT(M2)

2. **Baseline 2: NO CoT**
   - cot 없이 질문.
   - **두 모델 모두 실행** → NO-CoT(M1), NO-CoT(M2)

3. **Proposed: A2A Protocol**
   - Agent 1 (Planner): 문제 분해, 필요한 subtask 식별
   - Agent 2 (Solver): subtask 수행 후 concise output 생성
   - 필요 시 Agent 1이 replan 또는 stop
   - **두 모델 모두 같은 구조로 실행** → A2A(M1), A2A(M2)

→ 이렇게 하면 모델 축과 프로토콜 축이 교차해서 **2×3** 표를 만들 수 있다.

데이터셋은 openai/gsm8k을 적당히 사용 -> Huggingface cli 로그인 해뒀슴. 그런데 이랃ㄴ 

-> 그런데 문제1. 어떻게 어떤 지표로 평가할 것인가. 그리고 실험 빨리 만들어서 해줘. 
