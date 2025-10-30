# CoT vs A2A Protocol Token Efficiency Comparison

OpenRouter를 통한 Claude Haiku 4.5 및 GPT-5o-mini 모델 대상 CoT vs A2A 프로토콜 토큰 효율성 비교 실험

## 프로젝트 구조

```
cotvsa2a/
├── src/
│   ├── a2a/              # A2A FastAPI 서버
│   │   └── server.py
│   ├── baseline/         # CoT/NO-CoT 베이스라인
│   │   └── cot_baseline.py
│   ├── experiments/      # 실험 실행 스크립트
│   │   ├── run_gsm8k.py
│   │   └── run_hotpotqa.py
│   ├── shared/           # 공통 모듈
│   │   └── openrouter_client.py
│   └── utils/            # 유틸리티
│       ├── dataset_loader.py
│       └── evaluator.py
├── results/              # 실험 결과 저장 디렉토리 (자동 생성)
├── requirements.txt
└── .env                  # API 키 설정
```

## 설치

### 1. 가상환경 설정

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일에 OpenRouter API 키 설정:

```env
OPENROUTER_API_KEY_A2A_PLAN_CLAUDE=your_key_here
OPENROUTER_API_KEY_A2A_SOLVER_CLAUDE=your_key_here
OPENROUTER_API_KEY_A2A_PLAN_GPT=your_key_here
OPENROUTER_API_KEY_A2A_SOLVER_GPT=your_key_here
OPENROUTER_API_KEY_COT_GPT=your_key_here
OPENROUTER_API_KEY_COT_CLAUDE=your_key_here
OPENROUTER_API_KEY_NO_COT_GPT=your_key_here
OPENROUTER_API_KEY_NO_COT_CLAUDE=your_key_here
```

## 실행 방법

### 1. A2A 서버 시작

```bash
python src/a2a/server.py
```

서버는 `http://localhost:8100` 에서 실행됩니다.

### 2. 실험 실행

**터미널 1: A2A 서버 실행**
```bash
python src/a2a/server.py
```

**터미널 2: GSM8K 실험**
```bash
python src/experiments/run_gsm8k.py
```

**터미널 3: HotpotQA 실험**
```bash
python src/experiments/run_hotpotqa.py
```

## 실험 구성

### 데이터셋
- **GSM8K**: 200개 샘플 (수학 추론)
- **HotpotQA**: 100개 샘플 (다중 홉 질문응답)

### 비교 대상
1. **NO-CoT**: CoT 프롬프팅 없이 직접 답변
2. **CoT**: "Let's think step by step" CoT 프롬프팅
3. **A2A**: Planner + Solver 에이전트 프로토콜

### 모델
- `claude`: anthropic/claude-4.5-haiku
- `gpt`: openai/gpt-5o-mini

### 평가 지표
- **Accuracy**: 정답률
- **Total Tokens**: 총 토큰 사용량 (입력 + 출력)
- **Avg Tokens per Sample**: 샘플당 평균 토큰
- **Efficiency**: Accuracy / (Avg Tokens / 1000)
- **Prompt/Completion Tokens**: 입력/출력 토큰 분리 통계

## 결과 확인

실험 완료 후 `results/` 디렉토리에 생성:

- `*_raw.json`: 각 샘플별 상세 결과
- `*_metrics.json`: 집계된 메트릭
- `*_results.csv`: CSV 포맷 결과
- `*_summary.txt`: 사람이 읽기 쉬운 요약

## API 엔드포인트

### A2A 서버

**POST /a2a/run**
```json
{
  "question": "What is 2+2?",
  "context": "optional context",
  "model_name": "claude",
  "dataset": "gsm8k"
}
```

**Response**
```json
{
  "answer": "The answer is 4",
  "total_tokens": 150,
  "prompt_tokens": 100,
  "completion_tokens": 50,
  "steps": [...]
}
```

**GET /health**
```json
{"status": "ok"}
```

## 주의사항

1. OpenRouter API 키는 각 실험 유형별로 분리하여 비용 추적 용이
2. 실험 실행 전 A2A 서버가 반드시 실행 중이어야 함
3. 대규모 실험이므로 API 비용 발생에 주의
4. 데이터셋 로딩 시 HuggingFace 로그인 필요할 수 있음
