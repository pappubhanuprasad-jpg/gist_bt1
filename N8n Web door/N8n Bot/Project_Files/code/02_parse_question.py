# =============================================================================
# Parse Question  --  reads the POST body from the web page, checks it, and
# prepares the two fields the agent needs: question and session_id.
#
# Code node:  Language = Python (Native)      Mode = Run Once for All Items
#
# No imports. n8n Cloud blocks every Python import, standard library included,
# so this node uses plain Python only.
# =============================================================================

MAX_LEN = 400
GREETINGS = ["hi", "hello", "hey", "hai", "namaste", "good morning",
             "good afternoon", "good evening", "start", "thanks", "thank you"]

out = []

for item in _items:
    body = item["json"].get("body") or {}

    question = str(body.get("question") or "").strip()
    question = " ".join(question.split())[:MAX_LEN]   # squeeze every run of spaces

    session = str(body.get("session_id") or "").strip()[:64] or "web-guest"

    probe = question.lower().strip(" .!?")
    ok = True
    reason = ""

    if question == "":
        ok, reason = False, "empty"
    elif len(question) < 3:
        ok, reason = False, "too_short"
    elif probe in GREETINGS:
        ok, reason = False, "greeting"

    out.append({
        "json": {
            "ok": ok,
            "reason": reason,
            "question": question,
            "session_id": session,
        }
    })

return out
