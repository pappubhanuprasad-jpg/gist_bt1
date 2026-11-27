# GIST College Assistant (n8n Bot) — Clear Setup & Integration Guide

This folder contains the **n8n RAG College Information Assistant** workflow and
all files needed to incorporate it into the **GIST SMS** FastAPI application
(`c:\COlleg SMS`).

---

## 1. Current Repository Status

Before following the steps below, know what is already in place vs. pending:

- **Staged in `N8n Bot/` (not yet wired into `app/`):**
  - `N8n Bot/Integration/Project_Files/sms_integration/app/routers/assistant.py`
  - `N8n Bot/Integration/Project_Files/sms_integration/app/templates/partials/assistant_widget.html`
  - `N8n Bot/Integration/Project_Files/sms_integration/app/static/css/assistant.css`
  - `N8n Bot/Integration/Project_Files/sms_integration/app/static/js/assistant.js`
- **Not yet applied to GIST SMS root:**
  - `httpx` is not yet in `requirements.txt` or `venv`.
  - `app/config.py`, `app/main.py`, `app/templates/base.html`, and `app/templates/base_public.html` do not yet include the assistant settings, router, or widget partial.
  - `.env` does not yet have the four `ASSISTANT_*` variables.
  - `.env` and `sms.db` are currently still tracked in git (see Phase 3 below).

---

## 2. Folder Map (What Each File Is For)

```text
N8n Bot/
├── GIST_College_Assistant_Complete_Guide.docx <-- Single consolidated Word guide (n8n + prompts + integration + tests)
├── README.md                                  <-- Plain-Markdown master guide
├── TESTING_COMMANDS.md                        <-- Ready-to-run PowerShell & curl.exe tests (GET + POST)
├── PROMPTS_FOR_CODING_ASSISTANT.md            <-- Prompts if delegating integration to an AI assistant
├── Day4_College_Assistant_Build_Guide.docx    <-- Original Day 4 Word doc (building n8n workflow)
│
├── Integration/
│   ├── Day4_SMS_Chatbot_Build_Guide.docx      <-- Reference Word doc for SMS integration
│   ├── 06_Diagrams/SMS_chatbot_architecture.png
│   └── Project_Files/sms_integration/         <-- Actual files to copy into GIST SMS
│       ├── README_INTEGRATION.md              <-- Architecture, boundary & troubleshooting
│       ├── INTEGRATION_PATCHES.md             <-- Exact file copies + 5 codebase edits
│       ├── .env.example                       <-- 4 ASSISTANT_* environment lines
│       └── app/...                            <-- 4 files to copy into c:\COlleg SMS\app\
│
└── Project_Files/                             <-- n8n workflow assets & standalone demo
    ├── 01_n8n_Workflow/College_Information_Assistant_BACKUP.json
    ├── College_Handbook_SAMPLE.md             <-- Sample college knowledge base (11 sections)
    ├── System_Prompt.txt                      <-- System prompt for both AI Agent nodes
    ├── Test_Questions.txt                     <-- 17 functional & refusal test questions
    ├── code/                                  <-- 6 n8n Python Code nodes + test_code_nodes.py (60 checks)
    └── web/                                   <-- Standalone HTML demo (NOT used once SMS widget is active)
```

> **Note on `.docx` guides:** `Day4_College_Assistant_Build_Guide.docx` mentions
> `55 checks` for `test_code_nodes.py`, whereas the current script runs **60 checks**.
> The Markdown docs (`README.md`, `TESTING_COMMANDS.md`, `INTEGRATION_PATCHES.md`,
> `README_INTEGRATION.md`) are the up-to-date reference for this repository.

---

## 3. Complete Step-by-Step Incorporation Plan

### Phase 1 · Set Up & Activate the n8n Cloud Workflow

1. **Import workflow:** In n8n Cloud, import
   `N8n Bot/Project_Files/01_n8n_Workflow/College_Information_Assistant_BACKUP.json`.
   (Set workflow timezone to `Asia/Kolkata`.)
2. **Create and attach the 4 credentials** (replacing every `"REPLACE"` credential placeholder):
   - **OpenAi** → name it `OpenAi account` (used by `Chat Model (GPT-4o-mini)`).
   - **Mistral Cloud API** → name it `Mistral Cloud account` (used by `Ingest Embeddings`, `Tool Embeddings`, and `Fallback Model (Mistral)`).
   - **Header Auth** → name it `College Webhook Key` with:
     - **Name:** `x-college-key` (exact header name, lowercase, no spaces)
     - **Value:** a strong random string (24+ characters)
   - **Telegram API** *(optional, only for Stage 3 Telegram)* → name it `Telegram College Bot`.
3. **Run Stage 1 (Build Vector Store):**
   - Click **Execute workflow** on **Start Ingest**.
   - Confirm `College Handbook` outputs 11 items and `Store Handbook` inserts documents into memory key `college_handbook`.
   - *Important:* Simple Vector Store is in-memory only. Re-run **Start Ingest** any time your n8n Cloud instance restarts.
4. **Publish / Activate the workflow:**
   - Toggle the workflow **Active / Published** in n8n so the **Production URL**
     (`https://<your-instance>.app.n8n.cloud/webhook/college-ask`) responds continuously.
   - *(Test URL `/webhook-test/college-ask` only answers one request after clicking Execute workflow.)*

---

### Phase 2 · Incorporate the Bot into GIST SMS (`c:\COlleg SMS`)

Run all commands from `c:\COlleg SMS`:

1. **Copy the 4 files** into `app/`:
   ```powershell
   New-Item -ItemType Directory -Force -Path "app\templates\partials" | Out-Null
   Copy-Item "N8n Bot\Integration\Project_Files\sms_integration\app\routers\assistant.py" "app\routers\assistant.py"
   Copy-Item "N8n Bot\Integration\Project_Files\sms_integration\app\templates\partials\assistant_widget.html" "app\templates\partials\assistant_widget.html"
   Copy-Item "N8n Bot\Integration\Project_Files\sms_integration\app\static\css\assistant.css" "app\static\css\assistant.css"
   Copy-Item "N8n Bot\Integration\Project_Files\sms_integration\app\static\js\assistant.js" "app\static\js\assistant.js"
   ```
2. **Add `httpx` to `requirements.txt` and install it in `venv`:**
   ```powershell
   Add-Content -Path "requirements.txt" -Value "`nhttpx"
   .\venv\Scripts\python.exe -m pip install httpx
   ```
3. **Apply the remaining 4 code edits** shown in
   [Integration/Project_Files/sms_integration/INTEGRATION_PATCHES.md](Integration/Project_Files/sms_integration/INTEGRATION_PATCHES.md):
   - `app/config.py` (add `ASSISTANT_ENABLED`, `ASSISTANT_URL`, `ASSISTANT_KEY`, `ASSISTANT_TIMEOUT`, and non-raising empty-URL warning)
   - `app/main.py` (import `assistant_router`, set `templates.env.globals["assistant_enabled"] = settings.ASSISTANT_ENABLED`, call `app.include_router(assistant_router)`)
   - `app/templates/base.html` (include `partials/assistant_widget.html` before `</body>`)
   - `app/templates/base_public.html` (include `partials/assistant_widget.html` before `</body>`)
4. **Add the 4 `ASSISTANT_*` variables to your local `.env`** (see
   [Integration/Project_Files/sms_integration/.env.example](Integration/Project_Files/sms_integration/.env.example)):
   ```env
   ASSISTANT_ENABLED=true
   ASSISTANT_URL=https://your-instance.app.n8n.cloud/webhook/college-ask
   ASSISTANT_KEY=your-x-college-key-value
   ASSISTANT_TIMEOUT=30
   ```
5. **Start / restart FastAPI:**
   ```powershell
   .\venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```

---

### Phase 3 · Security & Post-Integration Cleanup

1. **Remove CORS `*` from n8n Ask Webhook:** Once the GIST SMS widget works,
   remove `Allowed Origins (CORS) = *` from the **Ask Webhook** node in n8n
   because the browser only calls `POST /assistant/ask` on `127.0.0.1:8000`
   (same origin).
2. **Stop tracking `.env` and `sms.db` in git:**
   - Add `.env` and `sms.db` to `.gitignore`.
   - Run `git rm --cached .env sms.db` (keeps local files on disk).
   - Add a root `.env.example` with placeholders only (all 5 core settings + 4 `ASSISTANT_*` settings).
   - Rotate `SECRET_KEY` in local `.env` (since the previous key exists in git history).

---

## 4. Important Facts & Design Notes

1. **HTTP Methods (`GET` vs `POST`):**
   - All GIST SMS pages, health check, static assets, and tracking views use **`GET`**
     (e.g., `GET /health`, `GET /login`, `GET /register`, `GET /register/status?reference_no=...`,
     `GET /student`, `GET /hod`, `GET /hod/registrations`).
   - The chatbot endpoint is **`POST`-only**: `POST /assistant/ask` (and n8n webhook is `POST /webhook/college-ask`).
     Calling `GET /assistant/ask` returns `405 Method Not Allowed`.
2. **Privacy boundary:** `app/routers/assistant.py` never sends user ID, roll
   number, name, role, or `access_token` to n8n — only `question` (max 400 chars)
   and an opaque `assistant_sid` cookie (`sms-...`).
3. **Sample Handbook vs Seeded Database figures:**
   `College_Handbook_SAMPLE.md` uses classroom demo numbers (e.g., CSE intake `180`,
   HOD `Dr. P. Lakshmi Narayana`), whereas `scripts/seed.py` seeds `sms.db` with
   `intake=120` for all 5 departments and demo HOD names (`Dr. Anjali Sharma`, etc.).
   Update the **College Handbook** node in n8n and re-run Stage 1 when switching
   to real institutional data.
4. **Where the widget renders:** Every page extending `base.html` or
   `base_public.html` renders the widget when `ASSISTANT_ENABLED` is `true` and
   `ASSISTANT_URL` is non-empty. SQLADMIN (`/admin`) uses its own template
   environment and intentionally does not show the widget.

---

## 5. Verification & Testing

Run the automated checks and full `GET` + `POST` endpoint commands in
[TESTING_COMMANDS.md](TESTING_COMMANDS.md), and test the 17 behavioral prompts in
[Project_Files/Test_Questions.txt](Project_Files/Test_Questions.txt).
