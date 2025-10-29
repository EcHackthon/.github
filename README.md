# AI Mood DJ 백엔드 오케스트레이터

이 프로젝트는 Gemini CLI 대화, 감정 분류기, Spotify 추천, 그리고 백엔드 전달을 하나의 흐름으로 묶어 프런트엔드가 사용자의 감정에 맞는 음악을 제공할 수 있도록 돕습니다. Jason Mayes의 Web AI Spotify DJ 아이디어를 기반으로 하며, 해커톤에 적합하도록 파이썬식 OOP 구조로 재구성했습니다.

## 주요 기능
- **Gemini CLI 연동**: 프롬프트, 온도, 대화 이력 보존을 설정 가능.
- **감정 감지**: 명확한 신뢰도 점수를 제공하는 어휘 기반 휴리스틱 사용.
- **Spotify 추천**: 리프레시 토큰 인증과 감정별 시드 튜닝을 활용하며, 필요 시 지정한 플레이리스트를 백업 소스로 사용.
- **백엔드 전달**: 비밀 키를 노출하지 않고 트랙 정보를 웹 스택에 전달.
- **.env 예시 파일**: 필요한 모든 환경 변수를 안전하게 안내.
- **외부 런타임 의존성 최소화**: 표준 라이브러리를 활용한 경량 HTTP 클라이언트와 .env 로더 제공.

## 프로젝트 구조
```
.
├── main.py                   # 커맨드라인 진입점
├── prompts/                  # Gemini 시스템 프롬프트 및 퓨샷 예시
├── src/
│   ├── config.py             # 환경 변수 기반 설정 로더
│   ├── backend/
│   │   └── http_client.py    # 백엔드 페이로드 전송
│   ├── conversation/
│   │   ├── gemini_cli.py     # Gemini CLI 서브프로세스 래퍼
│   │   ├── mood_detector.py  # 감정 휴리스틱 분석
│   │   ├── orchestrator.py   # 대화 → 감정 → Spotify 흐름 오케스트레이션
│   │   └── prompt_loader.py  # 프롬프트 파일 유틸리티
│   └── spotify/
│       ├── auth.py           # Spotify OAuth 리프레시 토큰 헬퍼
│       ├── client.py         # 추천 조회
│       └── recommendation.py # 요청/응답 데이터 구조
└── .env.example              # 비밀 설정 템플릿
```

## 시작하기
1. Python 3.11 가상환경을 만들고 선택 사항인 개발 의존성을 설치합니다.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. `.env.example`을 `.env`로 복사한 뒤 Spotify와 Gemini 시크릿을 채웁니다.
3. [Gemini CLI](https://ai.google.dev/gemini-api/docs/get-started)가 설치되어 있고 원하는 프로필로 설정되어 있는지 확인합니다.
4. 다음 명령으로 샘플 상호작용을 실행합니다.
   ```bash
   python main.py --message "오늘 하루가 왜 이렇게 지루하지?" --emit-backend
   ```

## 백엔드 페이로드 규약
`--emit-backend` 옵션을 사용하면 애플리케이션이 `BACKEND_RECOMMENDATION_ENDPOINT`로 다음 형태의 JSON 페이로드를 POST합니다.
```json
[
  {
    "user_message": "...",
    "ai_response": "...",
    "mood": "positive",
    "confidence": 0.78,
    "rationale": "Detected 7 positive words out of 9 mood keywords.",
    "recommendations": [
      {
        "mood": "positive",
        "rationale": "Detected 7 positive words out of 9 mood keywords.",
        "tracks": [
          {
            "id": "3n3Ppam7vgaVa1iaRUc9Lp",
            "name": "Mr. Brightside",
            "artists": ["The Killers"],
            "preview_url": "https://p.scdn.co/mp3-preview/...",
            "external_url": "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"
          }
        ]
      }
    ]
  }
]
```
백엔드는 이 ID를 Spotify 재생이나 데이터베이스 항목으로 바로 매핑할 수 있습니다.

## 보안 고려 사항
- 비밀 값은 `.env`( `.gitignore`에 포함) 내에 유지되므로 로컬에서 직접 생성해야 합니다.
- HTTP 요청 시 `BACKEND_API_KEY` 헤더를 추가하여 제로 트러스트 배포를 지원합니다.
- Spotify 액세스 토큰은 메모리에 캐싱되며 리프레시 토큰을 통해 안전하게 갱신됩니다.

## 테스트
`tests/` 디렉터리에 테스트를 추가하고 `pytest`로 실행하세요. 감정 감지 휴리스틱이나 Spotify 파라미터 생성 로직을 검증하는 예제를 확장할 수 있습니다.
