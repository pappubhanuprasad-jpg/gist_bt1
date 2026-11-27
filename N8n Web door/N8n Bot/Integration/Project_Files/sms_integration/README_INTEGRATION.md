# The College Assistant inside GIST SMS

The Day 4 n8n RAG assistant embedded directly into the GIST Student Management
System (`c:\COlleg SMS`). A floating chat bubble appears in the bottom-right
corner of every public page (`/login`, `/register`, `/register/status`,
`/change-password`) and all five role dashboards (`/management`, `/hod`,
`/mentor`, `/trainer`, `/student`).

The FastAPI app runs locally (`http://127.0.0.1:8000`). The n8n workflow runs in
n8n Cloud. Only the FastAPI server talks to n8n — the browser never sees
`ASSISTANT_URL` or `ASSISTANT_KEY`.

```text
   Browser (localhost:8000)         FastAPI Server                    n8n Cloud
  ─────────────────────────        ────────────────                  ───────────
  Chat widget  ──POST /assistant/ask──▶  app/routers/assistant.py  ──POST + x-college-key──▶  Ask Webhook
               ◀──────JSON {ok,answer}──  reads .env, rate-limits                             Agent + RAG
                                          sends only {question, session_id}                   ◀── answer
```

---

## Why integrate into GIST SMS instead of `Project_Files/web/index.html`

| Aspect | Standalone `web/index.html` | Integrated into GIST SMS |
|---|---|---|
| Where `ASSISTANT_KEY` lives | Browser `localStorage` (visible in DevTools) | Server `.env` only (never sent to browser) |
| CORS on n8n Webhook | Required `Allowed Origins = *` | Not needed — same-origin call to `/assistant/ask` |
| Who can call n8n directly | Anyone with the URL and key | Only the FastAPI server |
| Rate limiting | None | 25 questions per `assistant_sid` cookie per 10 minutes |
| Placement | Separate browser tab | Bottom-right widget on public and dashboard pages |

Once GIST SMS integration is working, **remove** `Allowed Origins (CORS)` from
the **Ask Webhook** node in n8n.

---

## Quick install steps (from `c:\COlleg SMS`)

For full line-by-line patch details and PowerShell commands, see
[INTEGRATION_PATCHES.md](INTEGRATION_PATCHES.md) and the top-level guide
[N8n Bot/README.md](../../../README.md).

1. **Set up n8n Cloud first:**
   - Import `N8n Bot/Project_Files/01_n8n_Workflow/College_Information_Assistant_BACKUP.json`.
   - Connect credentials (`OpenAi account`, `Mistral Cloud account`, `College Webhook Key` with header name `x-college-key`, and optionally `Telegram College Bot`).
   - Click **Execute workflow** on **Start Ingest** (Stage 1) to load the handbook vectors into `college_handbook`.
   - **Publish / Activate** the workflow so the Production URL (`/webhook/college-ask`) stays live.
2. **Copy the 4 files** from `N8n Bot/Integration/Project_Files/sms_integration/app/` into `app/` (creating `app/templates/partials/`).
3. **Apply the 5 edits** to `requirements.txt`, `app/config.py`, `app/main.py`, `app/templates/base.html`, and `app/templates/base_public.html` (exact snippets in [INTEGRATION_PATCHES.md](INTEGRATION_PATCHES.md)).
4. **Install `httpx` in the workspace `venv`:**
   ```powershell
   .\venv\Scripts\python.exe -m pip install httpx
   ```
5. **Add the 4 `ASSISTANT_*` lines to `.env`** (see `.env.example` in this folder).
6. **Start (or restart) FastAPI:**
   ```powershell
   .\venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```
7. **Test in browser:** open `http://127.0.0.1:8000/login`, click the chat bubble
   in the bottom-right, and try *"What is the fee structure for B.Tech?"*.

---

## Endpoint behavior: `GET` vs `POST`

- **GIST SMS pages & data lookup use `GET`** (for example `GET /health`, `GET /login`,
  `GET /register`, `GET /register/status?reference_no=REG-2026-00001`,
  `GET /student`, `GET /hod/registrations`, `GET /static/css/assistant.css`,
  `GET /static/js/assistant.js`).
- **The chatbot proxy route is `POST`-only:** `POST /assistant/ask` accepting JSON
  `{"question": "..."}` and returning `{"ok": true|false, "answer": "..."}`.
  Sending `GET /assistant/ask` returns `405 Method Not Allowed`.
- See [TESTING_COMMANDS.md](../../../TESTING_COMMANDS.md) for copy-paste
  PowerShell and `curl.exe` commands covering all `GET` routes and `POST` bot tests.

---

## The boundary between the dashboard and the assistant

- **The dashboard answers questions about YOU** (logged-in student/staff data from
  `sms.db`: roll number, mentor, registrations, department stats).
- **The assistant answers questions about the COLLEGE** (fees, intake, rules,
  departments, facilities from the n8n handbook). It never receives user IDs,
  roll numbers, names, roles, or auth tokens — only the sanitized question
  (max 400 chars) and an opaque `assistant_sid` cookie (`sms-<12 hex chars>`).

> **Sample handbook vs seeded DB note:** The sample handbook in `N8n Bot`
> (`College_Handbook_SAMPLE.md` / `01_college_handbook.py`) contains classroom
> sample figures (e.g., CSE intake `180`, sample HOD names like
> `Dr. P. Lakshmi Narayana`). Meanwhile `scripts/seed.py` seeds `sms.db` with
> `intake=120` per department and different demo HOD names. Replace the text in
> n8n's **College Handbook** node and re-run Stage 1 whenever you want the bot's
> figures to match your real college data.

---

## Switching off & troubleshooting

To disable the assistant without code changes, set `ASSISTANT_ENABLED=false` in
`.env` and restart `uvicorn`. The widget will not render (`assistant_enabled` is
`false`), and `POST /assistant/ask` returns HTTP 200 with
`{"ok": false, "answer": "The college assistant is not switched on..."}`.

| Symptom | Likely Cause | Fix |
|---|---|---|
| No chat bubble on `/login` or dashboards | `ASSISTANT_ENABLED=false`, empty `ASSISTANT_URL`, or missing `{% include %}` | Check uvicorn startup logs for warning; verify `base.html`, `base_public.html`, and `main.py` |
| No bubble inside `/admin` | Expected behavior | SQLADMIN uses its own template environment, not `base.html` |
| `"The college assistant is not switched on..."` | `ASSISTANT_URL` empty or `ASSISTANT_ENABLED=false` | Update `.env` and restart `uvicorn` |
| `"The assistant's access key was refused..."` | n8n returned `401`/`403` | Match `ASSISTANT_KEY` in `.env` with n8n Header Auth (`x-college-key`) |
| `"No workflow answered at that address..."` | n8n returned `404` | Publish/activate workflow or verify Production URL (`/webhook/college-ask`) |
| `"The workflow stopped with an error..."` | n8n returned `>=400` (`500`, etc.) | Open execution in n8n — usually Simple Vector Store is empty (re-run Stage 1) |
| `"The assistant took too long to answer..."` | Request timed out (`504`) | Raise `ASSISTANT_TIMEOUT` in `.env` or check n8n OpenAI/Mistral credentials |
| `"That is a lot of questions at once..."` | Hit rate limit (`429`) | Wait up to 10 minutes (25 questions per `assistant_sid` per 600s) |
| `ModuleNotFoundError: No module named 'httpx'` | `httpx` not installed in `venv` | Run `.\venv\Scripts\python.exe -m pip install httpx` |
