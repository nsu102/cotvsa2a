# A2A Quick Start Guide

## 1. Setup (1분)

```bash
# 가상환경 활성화
source venv/bin/activate

# 환경변수 확인
cat .env | grep A2A
```

## 2. 테스트 (1분)

```bash
# 간단한 테스트
python test_a2a_system.py
```

예상 출력:
```
Test 1: What is 15 + 27?
Final Answer: 42
Total Tokens: 390
Cards Generated: 3
```

## 3. 서버 실행 (백그라운드)

```bash
# 터미널 1: 서버 시작
python src/a2a_adk/run_server.py

# 터미널 2: API 테스트
curl -X POST http://localhost:8100/a2a/run \
  -H "Content-Type: application/json" \
  -d '{"question": "What is 2+2?", "model_name": "claude"}'
```

## 4. 전체 실험 (30-60분)

```bash
# MATH-500 500문제 실험
python src/experiments/run_math500.py
```

실험 순서:
1. No-CoT baseline (Claude) - 500문제
2. No-CoT baseline (GPT) - 500문제
3. CoT baseline (Claude) - 500문제
4. CoT baseline (GPT) - 500문제
5. A2A (Claude) - 500문제
6. A2A (GPT) - 500문제

총: 3000문제 풀이

## 5. 결과 확인

```bash
# 결과 디렉토리
ls -lh results/

# 메트릭 확인
cat results/math500_summary.json
```

예상 결과 파일:
- `math500_summary.json` - 전체 요약
- `math500_detailed.csv` - 문제별 상세
- `math500_a2a_claude_cards.json` - A2A 카드
- `math500_a2a_gpt_cards.json` - A2A 카드

## 주요 메트릭

```python
{
  "no_cot_claude": {
    "accuracy": 0.45,
    "avg_tokens": 150,
    "efficiency": 0.300
  },
  "cot_claude": {
    "accuracy": 0.65,
    "avg_tokens": 1200,
    "efficiency": 0.054
  },
  "a2a_claude": {
    "accuracy": 0.62,
    "avg_tokens": 500,
    "efficiency": 0.124
  }
}
```

## 트러블슈팅

### API 키 오류
```bash
# .env 파일 확인
cat .env | grep OPENROUTER_API_KEY

# 8개 키 모두 있는지 확인
```

### 서버 포트 충돌
```bash
# 8100 포트 사용 확인
lsof -i :8100

# 종료
kill -9 [PID]
```

### 토큰 제한
```bash
# max_tokens 조정 (solvers.py:38)
max_tokens=2000  # 기본값
```

## 빠른 검증 (5문제만)

```bash
# dataset_loader.py 수정
samples = DatasetLoader.load_math500(num_samples=5)  # 500 → 5

# 실험 실행
python src/experiments/run_math500.py
```

약 2-3분 소요 (5문제 × 6개 방법 = 30개 실행)
