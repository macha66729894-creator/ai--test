"""Slack 대화 구조화 봇.

사용법
  /구조화            -> 현재 채널 최근 메시지를 구조화
  /구조화 50         -> 최근 50개만
  스레드 안에서 /구조화 -> 해당 스레드만 구조화
  봇 멘션(@bot)       -> 스레드 안이면 그 스레드, 아니면 채널을 구조화

결과는 주제 / 핵심 요점 / 결정사항 / 액션아이템 / 미해결 질문 / 출처(원문 링크)로 정리됩니다.
"""
import os
import re

import anthropic
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])
claude = anthropic.Anthropic()
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "200"))

SYSTEM = """당신은 슬랙 대화를 구조화하는 분석가입니다.
입력은 '[번호] 작성자: 내용' 형식의 메시지 목록입니다. 아래 형식(슬랙 mrkdwn)으로만 한국어로 답하세요.
추측은 금지하고 대화에 근거한 내용만 쓰세요. 각 항목 끝에 근거 메시지 번호를 [3], [5] 처럼 붙이세요.

*📌 주제*
한 줄 요약
*🔑 핵심 요점*
• ...
*✅ 결정사항*
• ... (없으면 '없음')
*📋 액션아이템*
• 담당자 / 할 일 / 기한 (없으면 '없음')
*❓ 미해결 질문*
• ... (없으면 '없음')"""


def user_names(client, ids):
    names = {}
    for uid in ids:
        try:
            p = client.users_info(user=uid)["user"]
            names[uid] = p.get("real_name") or p.get("name") or uid
        except Exception:
            names[uid] = uid
    return names


def fetch_messages(client, channel, thread_ts=None, limit=MAX_MESSAGES):
    if thread_ts:
        res = client.conversations_replies(channel=channel, ts=thread_ts, limit=limit)
        msgs = res["messages"]
    else:
        res = client.conversations_history(channel=channel, limit=limit)
        msgs = list(reversed(res["messages"]))  # 오래된 순
    return [m for m in msgs if m.get("text") and not m.get("bot_id")]


def structure(client, channel, thread_ts=None, limit=MAX_MESSAGES):
    msgs = fetch_messages(client, channel, thread_ts, limit)
    if not msgs:
        return "구조화할 메시지가 없습니다."
    names = user_names(client, {m["user"] for m in msgs if "user" in m})
    lines = [
        f"[{i}] {names.get(m.get('user'), '?')}: {re.sub(r'\\s+', ' ', m['text'])}"
        for i, m in enumerate(msgs, 1)
    ]
    resp = claude.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM,
        messages=[{"role": "user", "content": "\n".join(lines)}],
    )
    body = resp.content[0].text
    # 출처: 원문 메시지 퍼머링크
    links = []
    for i, m in enumerate(msgs, 1):
        try:
            pl = client.chat_getPermalink(channel=channel, message_ts=m["ts"])["permalink"]
            links.append(f"<{pl}|[{i}]>")
        except Exception:
            pass
    src = "\n*🔗 출처(원문)* " + " ".join(links[:40]) if links else ""
    return f"{body}{src}\n_분석 대상: {len(msgs)}개 메시지_"


@app.command("/구조화")
def cmd(ack, command, client, respond):
    ack("정리 중입니다… ⏳")
    arg = (command.get("text") or "").strip()
    limit = int(arg) if arg.isdigit() else MAX_MESSAGES
    try:
        out = structure(client, command["channel_id"], limit=min(limit, MAX_MESSAGES))
    except Exception as e:
        out = f"오류: {e}"
    respond(text=out, response_type="in_channel")


@app.event("app_mention")
def mention(event, client, say):
    ts = event.get("thread_ts")
    try:
        out = structure(client, event["channel"], thread_ts=ts)
    except Exception as e:
        out = f"오류: {e}"
    say(text=out, thread_ts=ts or event["ts"])


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
