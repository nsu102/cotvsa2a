# Quick Start Guide

## 빠른 시작 (5분)

### 1단계: 환경 설정 확인
```bash
source venv/bin/activate
python test_setup.py
```

모든 API 키와 라이브러리가 제대로 설정되었는지 확인합니다.

### 2단계: A2A 서버 시작
```bash
python src/a2a/server.py
```

서버가 `http://localhost:8100` 에서 시작됩니다.

### 3단계: 실험 실행 (별도 터미널)

**GSM8K 실험 (200 샘플)**
```bash
source venv/bin/activate
python src/experiments/run_gsm8k.py
```

**HotpotQA 실험 (100 샘플)**
```bash
source venv/bin/activate
python src/experiments/run_hotpotqa.py
```

### 결과 확인
실험이 완료되면 `results/` 디렉토리에 결과 파일들이 생성됩니다:
- `*_summary.txt` - 사람이 읽기 쉬운 요약
- `*_metrics.json` - 상세 메트릭
- `*_results.csv` - 전체 결과 데이터

## A2A 프로토콜 구조

### Controller-Mediated A2A Pattern

```
User Question
    ↓
[Planner Agent]
    ↓ (분석 & JSON action 생성)
    ├─→ {"action": "call_solver", "subtask": "..."}
    │       ↓
    │   [FastAPI Controller]
    │       ↓
    │   [Solver Agent] → OpenRouter API
    │       ↓
    │   결과 반환
    │       ↓
    ├─→ [Planner Agent] (다시 분석)
    │
    └─→ {"action": "final_answer", "answer": "..."}
            ↓
        최종 답변
```

### 핵심 특징
1. **강제 협업**: 첫 턴에서 Planner가 반드시 Solver를 호출 (A2A 패턴 강제)
2. **체이닝 가능**: Planner가 여러 번 Solver를 호출하여 중간 결과 수집
3. **JSON 기반 통신**: 구조화된 action 포맷으로 의사소통
4. **데이터셋별 최적화**:
   - GSM8K: 3턴 (계산 단계별 처리)
   - HotpotQA: 5턴 (멀티홉 정보 추출)
5. **토큰 효율성**:
   - Solver는 최소 정보만 반환 (1문장)
   - Planner가 필요시에만 추가 호출

## 비교 실험 구조

각 데이터셋과 모델 조합에 대해 3가지 방법을 비교:

1. **NO-CoT**: CoT 프롬프팅 없이 직접 답변
2. **CoT**: "Let's think step by step" 프롬프팅
3. **A2A**: Controller-mediated 멀티 에이전트

| Dataset | Samples | Method | Model | Expected Outcome |
|---------|---------|--------|-------|------------------|
| GSM8K | 200 | NO-CoT, CoT, A2A | claude, gpt | A2A가 토큰 효율적 |
| HotpotQA | 100 | NO-CoT, CoT, A2A | claude, gpt | A2A가 토큰 효율적 |

## 트러블슈팅

### A2A 서버가 시작되지 않음
- `.env` 파일의 API 키 확인
- 포트 8100이 이미 사용 중인지 확인: `lsof -i :8100`

### 데이터셋 로딩 에러
- HuggingFace 로그인: `huggingface-cli login`
- 인터넷 연결 확인

### OpenRouter API 에러
- API 키 유효성 확인
- OpenRouter 대시보드에서 크레딧 잔액 확인

### 메모리 부족
- 샘플 수를 줄이기: `load_gsm8k(num_samples=50)` 등으로 수정

## 예상 실행 시간 및 비용

**GSM8K (200 samples)**
- NO-CoT: ~10분, $0.50-1.00
- CoT: ~15분, $1.00-2.00
- A2A: ~20분, $0.80-1.50

**HotpotQA (100 samples)**
- NO-CoT: ~8분, $0.40-0.80
- CoT: ~12분, $0.80-1.50
- A2A: ~15분, $0.70-1.20

**총 예상 비용**: $5-10 (모든 실험 포함)

## 다음 단계

실험 완료 후:
1. `results/*_summary.txt` 파일 검토
2. 토큰 효율성 비교 (Efficiency 지표)
3. 정확도 대 토큰 사용량 트레이드오프 분석
4. 논문/보고서 작성을 위한 데이터 활용
