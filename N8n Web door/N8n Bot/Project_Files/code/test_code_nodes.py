"""Runs each n8n Python Code node offline, the way n8n would.

n8n hands the node an _items list and expects a list of items back, so the
test binds _items, runs the file, and checks what it returns. The nodes import
nothing, because n8n Cloud blocks every Python import — if a node ever grows an
import line, this test fails on Cloud before the classroom does.

Run it with:  python3 test_code_nodes.py
"""
import pathlib, sys

HERE = pathlib.Path(__file__).parent


def run(filename, items):
    """Exec the node's source as n8n does, with _items bound and the final
    `return` turned into an assignment. The source is NOT re-indented: the
    handbook node holds a triple-quoted string whose own indentation matters."""
    src = (HERE / filename).read_text().rstrip()
    lines = src.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("return "):
            lines[i] = "_result = " + lines[i][len("return "):]
            break
    else:
        raise AssertionError(filename + " never returns anything")
    scope = {"_items": [{"json": j} for j in items]}
    exec(compile("\n".join(lines), filename, "exec"), scope)
    return scope["_result"]


passed = failed = 0


def check(label, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"FAIL  {label}\n      got  {got!r}\n      want {want!r}")


# ---------- 01 College Handbook ---------------------------------------------
docs = run("01_college_handbook.py", [{}])
check("handbook: documents built", len(docs) >= 11, True)
check("handbook: every document has text", all(d["json"]["text"].strip() for d in docs), True)
check("handbook: every document names its section",
      all(d["json"]["text"].startswith(d["json"]["section"]) for d in docs), True)
sections = [d["json"]["section"] for d in docs]
for must in ["2. Programmes offered and sanctioned intake",
             "3. Admissions and registration for a fresh batch",
             "4. Fees structure",
             "5. Semester details and examinations",
             "7. Departments, heads and faculty"]:
    check(f"handbook: has section {must!r}", must in sections, True)
check("handbook: chunk source is sample data",
      any("SAMPLE TRAINING DATA" in d["json"]["text"] for d in docs), True)

# ---------- 02 Parse Question -----------------------------------------------
def parse(body):
    return run("02_parse_question.py", [{"body": body}])[0]["json"]

r = parse({"question": "  What   is the   fee for CSE? ", "session_id": "web-7f3a"})
check("parse: whitespace squeezed", r["question"], "What is the fee for CSE?")
check("parse: accepted", r["ok"], True)
check("parse: session kept", r["session_id"], "web-7f3a")
check("parse: no stray fields", sorted(r), ["ok", "question", "reason", "session_id"])

check("parse: empty rejected", parse({"question": ""})["reason"], "empty")
check("parse: missing key rejected", parse({})["reason"], "empty")
check("parse: too short rejected", parse({"question": "ok"})["reason"], "too_short")
check("parse: greeting rejected", parse({"question": "Hi!"})["reason"], "greeting")
check("parse: namaste rejected", parse({"question": "namaste"})["reason"], "greeting")
check("parse: question with greeting word accepted",
      parse({"question": "hello, what is the hostel fee"})["ok"], True)
check("parse: no session falls back", parse({"question": "intake of ECE?"})["session_id"], "web-guest")
check("parse: long question capped",
      len(parse({"question": "a" * 900})["question"]), 400)
check("parse: three word question accepted", parse({"question": "CSE intake seats"})["ok"], True)

# ---------- 03 Format Answer ------------------------------------------------
def fmt(data):
    return run("03_format_answer.py", [data])[0]["json"]

r = fmt({"output": "## Fees\n\nThe **tuition fee** is 48,000 rupees.\n\n\n\nPaid in two parts."})
check("format: headings stripped", r["answer"].startswith("Fees"), True)
check("format: bold marks stripped", "**" not in r["answer"], True)
check("format: blank runs collapsed", "\n\n\n" not in r["answer"], True)
check("format: ok flag", r["ok"], True)
check("format: empty answer falls back",
      fmt({"output": "   "})["answer"].startswith("That is not in the college handbook"), True)
check("format: reads text field too", fmt({"text": "Intake is 180."})["answer"], "Intake is 180.")

# ---------- 04 Reject Reply -------------------------------------------------
def rej(reason):
    return run("04_reject_reply.py", [{"reason": reason}])[0]["json"]

check("reject: empty message", rej("empty")["answer"], "Please type a question about the college.")
check("reject: greeting lists topics", "registration" in rej("greeting")["answer"], True)
check("reject: unknown reason falls back", rej("whatever")["ok"], True)

# ---------- many items at once ----------------------------------------------
many = run("02_parse_question.py", [{"body": {"question": "fee structure"}},
                                    {"body": {"question": "hi"}}])
check("parse: handles several items", [i["json"]["ok"] for i in many], [True, False])

# ---------- 05 Parse Telegram Message ---------------------------------------
def tg(message):
    return run("05_parse_telegram.py", [{"message": message}])[0]["json"]

r = tg({"text": "  what is the  CSE intake ", "chat": {"id": 98765}, "from": {"first_name": "Ramya"}})
check("telegram: whitespace squeezed", r["question"], "what is the CSE intake")
check("telegram: accepted", r["ok"], True)
check("telegram: chat id kept as text", r["chat_id"], "98765")
check("telegram: session id namespaced", r["session_id"], "tg-98765")
check("telegram: name kept", r["first_name"], "Ramya")

check("telegram: /start is a greeting", tg({"text": "/start", "chat": {"id": 1}})["reason"], "greeting")
check("telegram: /help is a greeting", tg({"text": "/help", "chat": {"id": 1}})["reason"], "greeting")
check("telegram: sticker has no text", tg({"sticker": {"id": "x"}, "chat": {"id": 1}})["reason"], "empty")
check("telegram: voice note has no text", tg({"voice": {"id": "x"}, "chat": {"id": 1}})["reason"], "empty")
check("telegram: no name falls back", tg({"text": "fee structure", "chat": {"id": 1}})["first_name"], "there")
check("telegram: long message capped", len(tg({"text": "b" * 900, "chat": {"id": 1}})["question"]), 400)

# the update can arrive in more than one shape
def raw(update):
    return run("05_parse_telegram.py", [update])[0]["json"]

flat = raw({"message_id": 9, "text": "what is the CSE intake", "chat": {"id": 55},
            "from": {"first_name": "Ravi"}})
check("telegram: message object handed over directly", flat["ok"], True)
check("telegram: chat id found in the flat shape", flat["chat_id"], "55")

edited = raw({"update_id": 2, "edited_message": {"text": "fee structure", "chat": {"id": 7}}})
check("telegram: an edited message still parses", edited["question"], "fee structure")

cap = raw({"update_id": 3, "message": {"caption": "what is the hostel fee",
                                       "chat": {"id": 8}, "photo": [{"file_id": "x"}]}})
check("telegram: a caption counts as the question", cap["ok"], True)

check("telegram: reports the keys it received",
      raw({"update_id": 4, "message": {"text": "intake of ECE", "chat": {"id": 9}}})["update_keys"],
      ["message", "update_id"])

# ---------- 06 Telegram Welcome ---------------------------------------------
def wel(data):
    return run("06_telegram_welcome.py", [data])[0]["json"]

w = wel({"reason": "greeting", "first_name": "Ramya"})
check("welcome: greets by name", w["answer"].startswith("Hello Ramya."), True)
check("welcome: lists registration", "registration" in w["answer"], True)
check("welcome: lists fees", "fee structure" in w["answer"], True)
check("welcome: non-text message explained",
      wel({"reason": "empty", "first_name": "Ramya"})["answer"].startswith("I can read typed questions only"), True)
check("welcome: short message nudged",
      "a few more words" in wel({"reason": "too_short", "first_name": "A"})["answer"], True)
check("welcome: unknown reason still greets",
      wel({"reason": "", "first_name": "Ravi"})["answer"].startswith("Hello Ravi."), True)

# ---------- no node may import anything (n8n Cloud blocks every import) -----
for f in sorted(HERE.glob("0*.py")):
    bad = [ln.strip() for ln in f.read_text().split("\n")
           if ln.startswith("import ") or ln.startswith("from ")]
    check("no imports in " + f.name, bad, [])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
