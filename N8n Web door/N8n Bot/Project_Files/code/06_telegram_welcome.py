# =============================================================================
# Telegram Welcome  --  the reply for /start, /help, a greeting, or anything
# that is not a question (a sticker, a photo, a voice note).
# Code node:  Language = Python (Native)      Mode = Run Once for All Items
# No imports: n8n Cloud blocks them all.
# =============================================================================

TOPICS = (
    "- the college, the branches and the sanctioned intake\n"
    "- admission and registration for the new batch, and the documents to bring\n"
    "- the fee structure, instalments, hostel and transport charges\n"
    "- semesters, internal and external marks, attendance and supplementary exams\n"
    "- scholarships and fee reimbursement\n"
    "- departments, heads of department and faculty\n"
    "- library, laboratories, hostel, transport and placements"
)

NOT_TEXT = ("I can read typed questions only. Please type your question about "
            "the college.")

out = []

for item in _items:
    data = item["json"]
    name = data.get("first_name", "there")
    reason = data.get("reason", "")

    if reason == "empty":
        answer = NOT_TEXT
    elif reason == "too_short":
        answer = "That is a little short for me. Try asking in a few more words."
    else:
        answer = ("Hello " + name + ". I am the College Assistant. I answer from "
                  "the college handbook:\n\n" + TOPICS + "\n\nType your question "
                  "and I will look it up.")

    out.append({"json": {"ok": True, "answer": answer, "source": "College assistant"}})

return out
