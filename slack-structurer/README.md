# Slack 대화 구조화 봇

슬랙 채널/스레드 대화를 Claude로 읽어 **주제·핵심 요점·결정사항·액션아이템·미해결 질문**으로 구조화하고, 근거가 된 원문 링크(출처)를 함께 게시합니다.

## 설정
1. https://api.slack.com/apps → *Create New App* → Socket Mode 켜기(App-Level Token `xapp-`, scope `connections:write`).
2. Bot Token Scopes: `commands`, `app_mentions:read`, `channels:history`, `groups:history`, `users:read`, `chat:write`
3. Slash Command `/구조화` 추가, Event Subscriptions에 `app_mention` 구독 후 워크스페이스에 설치.
4. 봇을 대상 채널에 초대(`/invite @봇`).
5. 실행:
```bash
cp .env.example .env   # 토큰 입력
pip install -r requirements.txt
python app.py
```

## 사용
- `/구조화` · `/구조화 50` : 채널 최근 메시지
- 스레드에서 `@봇` : 해당 스레드 구조화
