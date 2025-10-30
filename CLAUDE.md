# 주석 없이 개발
# 필요한게 있으면 무조건 나한테 다시 물어봐 

## 현재 최신 openai 버젼은 gpt-5랑 claude haiku 4.5 가 맞아. 

## venv 사용하고 requirements.txt에 의존성 정리해줘 api들은 모두 openrouter을 통해서 부를게. a2a 프로토콜은 https://github.com/themanojdesai/python-a2a 와 fastapi 로컬 서버를 사용할거야 포트번호는 8100~ 써줘.

# 그리고 오픈라우터 비용을 제야하니까 
OPENROUTER_API_KEY_A2A_PLAN_CLAUDE=
OPENROUTER_API_KEY_A2A_SOLVER_CLAUDE=
OPENROUTER_API_KEY_A2A_PLAN_GPT=
OPENROUTER_API_KEY_A2A_SOLVER_GPT=
OPENROUTER_API_KEY_COT_GPT=
OPENROUTER_API_KEY_COT_CLAUDE=
OPENROUTER_API_KEY_NO_COT_GPT=
OPENROUTER_API_KEY_NO_COT_CLAUDE=

이 친구들 사용해서 만들어주고. .env 안에 있어.