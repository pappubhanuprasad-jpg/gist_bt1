# =============================================================================
# Format Answer  --  tidies what the agent wrote and shapes the JSON the web
# page and Telegram read. The page shows plain text, so markdown marks go.
#
# Code node:  Language = Python (Native)      Mode = Run Once for All Items
# No imports: n8n Cloud blocks them all.
# =============================================================================

NOT_FOUND = ("That is not in the college handbook I have. "
             "Please check with the college office for this one.")

out = []

for item in _items:
    data = item["json"]
    answer = str(data.get("output") or data.get("text") or "").strip()

    if answer == "":
        answer = NOT_FOUND

    clean = []
    blanks = 0
    for line in answer.split("\n"):
        line = line.rstrip()
        if line.lstrip().startswith("#"):              # drop markdown headings
            line = line.lstrip("# ").rstrip()
        line = line.replace("**", "").replace("__", "")  # drop bold marks
        if line.strip() == "":
            blanks += 1
            if blanks > 1:                              # never two blank lines
                continue
        else:
            blanks = 0
        clean.append(line)

    out.append({
        "json": {
            "ok": True,
            "answer": "\n".join(clean).strip(),
            "source": "College handbook (sample data)",
        }
    })

return out
