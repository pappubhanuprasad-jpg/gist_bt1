# =============================================================================
# Parse Telegram Message  --  the Telegram front door.
# Same job as Parse Question, but it reads a Telegram update instead of a POST
# body, and carries the chat id forward so the reply can be sent back.
#
# Code node:  Language = Python (Native)      Mode = Run Once for All Items
# No imports: n8n Cloud blocks them all.
# =============================================================================

MAX_LEN = 400
OPENERS = ["/start", "/help", "start", "help", "hi", "hello", "hey", "hai",
           "namaste", "good morning", "good afternoon", "good evening",
           "thanks", "thank you"]

out = []

for item in _items:
    root = item["json"] or {}

    # A Telegram update arrives as {"update_id": …, "message": {…}}, but an edit
    # or a channel post sits under a different key, and some setups hand this
    # node the message object itself. Accept all of them.
    message = (root.get("message")
               or root.get("edited_message")
               or root.get("channel_post")
               or root.get("edited_channel_post")
               or {})
    if not message and ("text" in root or "chat" in root or "caption" in root):
        message = root

    chat = message.get("chat") or {}
    sender = message.get("from") or {}

    # a photo or a forward can carry its words in caption rather than text
    question = str(message.get("text") or message.get("caption") or "").strip()
    question = " ".join(question.split())[:MAX_LEN]

    chat_id = str(chat.get("id") or "")
    first_name = str(sender.get("first_name") or "").strip() or "there"

    probe = question.lower().strip(" .!?")
    ok = True
    reason = ""

    if question == "":
        ok, reason = False, "empty"          # a photo, a sticker, a voice note
    elif probe in OPENERS:
        ok, reason = False, "greeting"
    elif len(question) < 3:
        ok, reason = False, "too_short"

    out.append({
        "json": {
            "ok": ok,
            "reason": reason,
            "question": question,
            "chat_id": chat_id,
            "first_name": first_name,
            "session_id": "tg-" + chat_id,
            # diagnostic: the top-level keys this node actually received.
            # Useful the first time Telegram is wired up; delete the line later.
            "update_keys": sorted([str(k) for k in root.keys()]),
        }
    })

return out
