# =============================================================================
# Reject Reply  --  the answer sent when the question never reached the agent.
#
# Code node:  Language = Python (Native)      Mode = Run Once for All Items
# No imports: n8n Cloud blocks them all.
# =============================================================================

MESSAGES = {
    "empty": "Please type a question about the college.",
    "too_short": "That is a little short for me. Try asking in a few more words.",
    "greeting": ("Hello. Ask me about the college, the branches and intake, "
                 "admission and registration, the fee structure, the semester "
                 "and examination rules, the departments and faculty, the "
                 "hostel, transport or the library."),
}

DEFAULT = "Please type a question about the college."

out = []

for item in _items:
    reason = item["json"].get("reason", "")
    out.append({
        "json": {
            "ok": True,
            "answer": MESSAGES.get(reason, DEFAULT),
            "source": "College assistant",
        }
    })

return out
