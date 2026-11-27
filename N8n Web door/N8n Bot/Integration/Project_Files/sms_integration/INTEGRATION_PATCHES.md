# Exact Integration Patches for GIST SMS

Apply these changes from the GIST SMS repository root (`c:\COlleg SMS`).
Five existing files change, and four new files are copied from
`N8n Bot/Integration/Project_Files/sms_integration/`.

> **Status note:** Check `git status` before starting. Out of the box in this
> repository, these patches have **not** been applied yet — `app/routers/assistant.py`
> and the widget files still live only inside `N8n Bot/Integration/Project_Files/sms_integration/`.

---

## Step 1 · Copy the four new files into `app/`

`app/templates/partials/` does not exist yet — create it first.

| Source (from repo root) | Destination in GIST SMS |
|---|---|
| `N8n Bot/Integration/Project_Files/sms_integration/app/routers/assistant.py` | `app/routers/assistant.py` |
| `N8n Bot/Integration/Project_Files/sms_integration/app/templates/partials/assistant_widget.html` | `app/templates/partials/assistant_widget.html` |
| `N8n Bot/Integration/Project_Files/sms_integration/app/static/css/assistant.css` | `app/static/css/assistant.css` |
| `N8n Bot/Integration/Project_Files/sms_integration/app/static/js/assistant.js` | `app/static/js/assistant.js` |

Windows PowerShell commands (run from `c:\COlleg SMS`):

```powershell
New-Item -ItemType Directory -Force -Path "app\templates\partials" | Out-Null
Copy-Item "N8n Bot\Integration\Project_Files\sms_integration\app\routers\assistant.py" "app\routers\assistant.py"
Copy-Item "N8n Bot\Integration\Project_Files\sms_integration\app\templates\partials\assistant_widget.html" "app\templates\partials\assistant_widget.html"
Copy-Item "N8n Bot\Integration\Project_Files\sms_integration\app\static\css\assistant.css" "app\static\css\assistant.css"
Copy-Item "N8n Bot\Integration\Project_Files\sms_integration\app\static\js\assistant.js" "app\static\js\assistant.js"
```

---

## Step 2 · Edit the five existing files

### 2.1 `requirements.txt` — add `httpx` and install into `venv`

The server route `POST /assistant/ask` calls n8n using `httpx`, which is not
currently in `requirements.txt` or `venv`.

Append one line at the end of `requirements.txt`:

```text
httpx
```

Then install it into the project virtual environment:

```powershell
.\venv\Scripts\python.exe -m pip install httpx
```

---

### 2.2 `app/config.py` — add four `ASSISTANT_*` settings

Inside `Settings.__init__`, directly after `self.ADMISSION_YEAR = int(...)` and
**before** `# Validate SECRET_KEY` (`if len(self.SECRET_KEY) < 32:`), add:

```python
        # ---- College Assistant (n8n) ----
        self.ASSISTANT_ENABLED = os.getenv(
            "ASSISTANT_ENABLED", "true"
        ).strip().lower() in ("1", "true", "yes")

        self.ASSISTANT_URL = os.getenv("ASSISTANT_URL", "").strip()

        self.ASSISTANT_KEY = os.getenv("ASSISTANT_KEY", "").strip()

        self.ASSISTANT_TIMEOUT = float(
            os.getenv("ASSISTANT_TIMEOUT", "30")
        )
```

Then, at the very end of `Settings.__init__` (after `if self.ADMISSION_YEAR < 2000:`),
add:

```python
        # The application must still run with no assistant configured.
        if self.ASSISTANT_ENABLED and not self.ASSISTANT_URL:
            print(
                "WARNING: ASSISTANT_ENABLED is true but ASSISTANT_URL is empty. "
                "The college assistant will stay switched off."
            )
            self.ASSISTANT_ENABLED = False
```

Note what is **not** there: no `raise`. A missing chatbot configuration must
never prevent GIST SMS from starting.

---

### 2.3 `app/main.py` — register the global flag and router

1. With the other router imports (around line 18, after `trainer_router`):

```python
from app.routers.assistant import router as assistant_router
```

2. Immediately after `app.state.templates = templates` (around line 52):

```python
# Every template can ask whether the chat widget should be drawn.
templates.env.globals["assistant_enabled"] = settings.ASSISTANT_ENABLED
```

3. Alongside the other `app.include_router(...)` calls (around line 107, before `setup_admin`):

```python
# College Assistant: the browser's only door to the n8n workflow
app.include_router(assistant_router)
```

> **Note on `/admin`:** `setup_admin(...)` uses SQLADMIN's own template
> environment (`sqladmin/base.html` and `app/templates/sqladmin/login.html`).
> That is intentional: the chat widget appears on all public pages and all five
> role dashboards, not inside `/admin`.

---

### 2.4 `app/templates/base.html` — include the widget on role dashboards

Immediately before `</body>` (after the Bootstrap `<script>` tag):

```jinja
{% include "partials/assistant_widget.html" %}
```

This adds the widget to all five role dashboards (`management`, `hod`, `mentor`,
`trainer`, `student`) and `403.html`.

---

### 2.5 `app/templates/base_public.html` — include the widget on public pages

Immediately before `</body>` (after the HTMX `<script>` tag):

```jinja
{% include "partials/assistant_widget.html" %}
```

This adds the widget to `/login`, `/register`, `/register/done/...`,
`/register/status`, `/register/status/edit/...`, and `/change-password`.

---

## Step 3 · Append these four lines to `.env`

Copy from `N8n Bot/Integration/Project_Files/sms_integration/.env.example` into
your root `.env` file (replace the URL and key with your n8n values):

```env
ASSISTANT_ENABLED=true
ASSISTANT_URL=https://your-instance.app.n8n.cloud/webhook/college-ask
ASSISTANT_KEY=paste-the-long-random-string-here
ASSISTANT_TIMEOUT=30
```

> **Important:** `.env` is loaded once at process startup. Stop and restart
> `uvicorn` after editing `.env` (`--reload` watches `.py` files, not `.env`).

---

## Step 4 · Security clean-up in git (do not skip before sharing/pushing)

In this repository right now, `.env` (which holds `SECRET_KEY`) and `sms.db`
are tracked in git. Before committing or pushing:

1. Add `.env` and `sms.db` to `.gitignore`.
2. Stop tracking them without deleting your local files:
   ```powershell
   git rm --cached .env sms.db
   ```
3. Create a root `.env.example` listing all 9 setting names with placeholder/empty
   values (`APP_NAME`, `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_MINUTES`,
   `ADMISSION_YEAR`, plus the 4 `ASSISTANT_*` variables). Never put real keys in it.
4. Generate a fresh `SECRET_KEY` (at least 32 characters) in your local `.env`
   because the old key remains in git commit history.

---

## Step 5 · Post-integration cleanup in n8n

Once the FastAPI widget works end-to-end:

1. In n8n, open the **Ask Webhook** node → **Options** → remove
   `Allowed Origins (CORS)` (`*`). Requests now come server-to-server from
   FastAPI (`POST /assistant/ask`), not directly from the browser.
2. Confirm the workflow is **Published / Active** (using `/webhook/college-ask`,
   not `/webhook-test/college-ask`) and **Stage 1 (`Start Ingest`)** has been
   executed since the last n8n Cloud restart.
