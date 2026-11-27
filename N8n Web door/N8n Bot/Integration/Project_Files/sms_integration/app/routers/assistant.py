# app/routers/assistant.py
"""College Assistant — the browser's only door to the n8n workflow.

The page never holds the n8n key. The browser posts to this route on the same
origin, this route adds the header and calls n8n, and the answer comes back.
Nothing about the logged-in user is sent to n8n: only the question and an
opaque conversation id.
"""

import time
import uuid

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import settings


router = APIRouter(prefix="/assistant", tags=["College Assistant"])

MAX_QUESTION = 400
WINDOW_SECONDS = 600          # ten minutes
MAX_IN_WINDOW = 25            # questions per conversation in that window
COOKIE = "assistant_sid"

# conversation id -> list of timestamps. In-memory on purpose: this runs on one
# laptop, and the counter resetting when the app restarts costs nothing.
_recent: dict[str, list[float]] = {}

OFF = ("The college assistant is not switched on. Set ASSISTANT_URL and "
       "ASSISTANT_KEY in the .env file and restart the application.")
SLOW = ("The assistant took too long to answer. Try once more — and check that "
        "the n8n workflow is active.")
BROKEN = ("The assistant could not be reached. Check that n8n is running and "
          "that ASSISTANT_URL points at the production webhook.")
BUSY = "That is a lot of questions at once. Give it a minute and ask again."


def _conversation_id(request: Request) -> str:
    """A random id per browser, so the chat remembers the last few turns.

    It is not the user id and it is not sent anywhere except n8n's memory key.
    """
    existing = request.cookies.get(COOKIE)
    if existing and len(existing) <= 64:
        return existing
    return "sms-" + uuid.uuid4().hex[:12]


def _too_many(conversation: str) -> bool:
    now = time.time()
    seen = [t for t in _recent.get(conversation, []) if now - t < WINDOW_SECONDS]
    seen.append(now)
    _recent[conversation] = seen
    if len(_recent) > 500:                      # keep the dict from growing forever
        for key in [k for k, v in _recent.items() if now - max(v) > WINDOW_SECONDS]:
            _recent.pop(key, None)
    return len(seen) > MAX_IN_WINDOW


def _reply(answer: str, request: Request, conversation: str, ok: bool = True,
           status: int = 200) -> JSONResponse:
    response = JSONResponse({"ok": ok, "answer": answer}, status_code=status)
    if request.cookies.get(COOKIE) != conversation:
        response.set_cookie(
            COOKIE, conversation,
            max_age=60 * 60 * 8, httponly=True, samesite="lax",
        )
    return response


@router.post("/ask")
async def ask(request: Request):
    conversation = _conversation_id(request)

    if not settings.ASSISTANT_ENABLED or not settings.ASSISTANT_URL:
        return _reply(OFF, request, conversation, ok=False)

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    question = " ".join(str(payload.get("question") or "").split())[:MAX_QUESTION]

    if not question:
        return _reply("Please type a question about the college.", request, conversation)

    if _too_many(conversation):
        return _reply(BUSY, request, conversation, ok=False, status=429)

    try:
        async with httpx.AsyncClient(timeout=settings.ASSISTANT_TIMEOUT) as client:
            answer = await client.post(
                settings.ASSISTANT_URL,
                json={"question": question, "session_id": conversation},
                headers={"x-college-key": settings.ASSISTANT_KEY},
            )
    except httpx.TimeoutException:
        return _reply(SLOW, request, conversation, ok=False, status=504)
    except httpx.HTTPError as exc:
        print(f"[assistant] cannot reach n8n: {exc!r}")
        return _reply(BROKEN, request, conversation, ok=False, status=502)

    if answer.status_code in (401, 403):
        print(f"[assistant] n8n refused the key ({answer.status_code})")
        return _reply("The assistant's access key was refused. Check ASSISTANT_KEY "
                      "against the Header Auth credential in n8n.",
                      request, conversation, ok=False, status=502)

    if answer.status_code == 404:
        return _reply("No workflow answered at that address. Check that the n8n "
                      "workflow is active and that ASSISTANT_URL is the production "
                      "webhook, not the test one.",
                      request, conversation, ok=False, status=502)

    if answer.status_code >= 400:
        print(f"[assistant] n8n returned {answer.status_code}: {answer.text[:300]}")
        return _reply("The workflow stopped with an error. Open the execution in "
                      "n8n and look at the node marked red.",
                      request, conversation, ok=False, status=502)

    try:
        data = answer.json()
    except ValueError:
        return _reply(BROKEN, request, conversation, ok=False, status=502)

    if isinstance(data, list):
        data = data[0] if data else {}

    text = str(data.get("answer") or data.get("output") or "").strip()

    if not text:
        return _reply("The workflow replied without an answer. Check that Format "
                      "Answer is the last node before Respond to Webhook.",
                      request, conversation, ok=False, status=502)

    return _reply(text, request, conversation)
