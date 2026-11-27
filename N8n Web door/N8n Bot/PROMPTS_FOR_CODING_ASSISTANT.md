# Prompts for building the chatbot into GIST SMS

Three prompts, to paste into whatever coding assistant you use — Claude Code,
Cursor, Copilot Chat, the chat window. Use them in order.

Prompt 1 applies the integration when you already have the
`sms_integration/` folder. Prompt 2 does the same from scratch, for someone
who has only the repository. Prompt 3 is the security clean-up, and it is the
one not to skip.

A note for the session, since this is a prompt engineering programme: each
prompt below sets the role, states the stack rather than letting it be guessed,
lists the constraints as "do not" lines, and ends with acceptance checks. The
"do not" lines are doing most of the work — without them an assistant will
cheerfully add React, invent a `/api/v1/` prefix, or put the key in the
template. Show the room the prompt and the diff side by side.

---

## Prompt 1 · Apply the integration from the provided folder

> You are working in the GIST_SMS repository: a FastAPI student management
> system with Jinja2 templates, Bootstrap 5.3, SQLModel over SQLite, and
> cookie-based JWT auth with five roles (management, hod, mentor, trainer,
> student). It runs locally with `.\venv\Scripts\python.exe -m uvicorn app.main:app --reload`.
>
> The chatbot integration files are staged in
> `N8n Bot/Integration/Project_Files/sms_integration/`. Apply them to the repository.
>
> Copy these four files from `N8n Bot/Integration/Project_Files/sms_integration/`,
> creating `app/templates/partials/`:
>
> - `N8n Bot/Integration/Project_Files/sms_integration/app/routers/assistant.py` → `app/routers/assistant.py`
> - `N8n Bot/Integration/Project_Files/sms_integration/app/templates/partials/assistant_widget.html` → `app/templates/partials/assistant_widget.html`
> - `N8n Bot/Integration/Project_Files/sms_integration/app/static/css/assistant.css` → `app/static/css/assistant.css`
> - `N8n Bot/Integration/Project_Files/sms_integration/app/static/js/assistant.js` → `app/static/js/assistant.js`
>
> Then make exactly these five edits:
>
> 1. `requirements.txt`: add a line `httpx` (and install it in `venv` via `.\venv\Scripts\python.exe -m pip install httpx`).
> 2. `app/config.py`, inside `Settings.__init__`, after the `ADMISSION_YEAR`
>    block and before the `SECRET_KEY` length check, add settings
>    `ASSISTANT_ENABLED` (bool from env, default true), `ASSISTANT_URL` (str,
>    default empty), `ASSISTANT_KEY` (str, default empty) and
>    `ASSISTANT_TIMEOUT` (float, default 30). At the end of `__init__`, if
>    `ASSISTANT_ENABLED` is true and `ASSISTANT_URL` is empty, print a warning
>    and set `ASSISTANT_ENABLED` to false.
> 3. `app/main.py`: import the assistant router, add
>    `templates.env.globals["assistant_enabled"] = settings.ASSISTANT_ENABLED`
>    immediately after `app.state.templates = templates`, and include the
>    router alongside the others.
> 4. `app/templates/base.html`: add
>    `{% include "partials/assistant_widget.html" %}` immediately before
>    `</body>`.
> 5. `app/templates/base_public.html`: the same line, in the same place.
>
> Do not change anything else. Do not reformat files you are editing, do not
> reorder imports, do not rename anything, and do not touch any router, model
> or template other than the two base templates.
>
> Do not raise an exception when the assistant settings are missing — the
> student management system must still start without them.
>
> When you are done, show me the diff for the five edited files and list the
> four files you created.

---

## Prompt 2 · Build it from scratch, with only the repository

Use this if you do not have the `sms_integration` folder.

> You are working in the GIST_SMS repository: a FastAPI student management
> system with Jinja2 templates, Bootstrap 5.3, SQLModel over SQLite, and
> cookie-based JWT auth with five roles. It runs locally at
> `http://127.0.0.1:8000`. Read `app/main.py`, `app/config.py`,
> `app/templates/base.html`, `app/templates/base_public.html` and
> `app/static/css/app.css` before you write anything.
>
> Add a college information chatbot to the application. It answers questions
> about the college — fees, intake, admission and registration, semester
> rules, departments, hostel and transport — by calling an n8n workflow that
> already exists. The workflow is an HTTP POST endpoint that takes
> `{"question": "...", "session_id": "..."}` with a header `x-college-key`,
> and returns `{"ok": true, "answer": "...", "source": "..."}`.
>
> Build it as follows.
>
> **A server-side route.** `POST /assistant/ask` in a new file
> `app/routers/assistant.py`, registered in `app/main.py`. It reads the
> question from the JSON body, calls the n8n URL with `httpx` and the header,
> and returns `{"ok": bool, "answer": str}`. The n8n address and key come from
> settings, which come from `.env`. Requirements:
>
> - The browser must never receive the n8n URL or the key. They stay on the
>   server. This is the whole reason the route exists.
> - Send n8n nothing about the user: only the question and an opaque
>   conversation id kept in an HttpOnly cookie. No user id, no roll number, no
>   name, no role, no session token.
> - The route works whether or not anyone is logged in, because it also serves
>   the public login and registration pages.
> - Limit one conversation to 25 questions in ten minutes, in memory.
> - Trim the question to 400 characters and squeeze repeated whitespace.
> - Turn every failure into one plain sentence a non-technical person can act
>   on — timeout, connection error, 401/403 (key refused), 404 (workflow not
>   active or test URL), any other 4xx/5xx, and a reply with no answer field.
>   Print the real error to the server log; never send a stack trace to the
>   browser.
>
> **Four settings** in `app/config.py`, read from the environment with
> `os.getenv` like the existing ones: `ASSISTANT_ENABLED` (bool, default true),
> `ASSISTANT_URL` (str), `ASSISTANT_KEY` (str), `ASSISTANT_TIMEOUT` (float,
> default 30). If enabled but the URL is empty, print a warning and switch the
> feature off. Do not raise — a missing chatbot must not stop the system
> starting, unlike the existing `SECRET_KEY` check, which should stay as it is.
>
> **A widget**, as `app/templates/partials/assistant_widget.html`, included
> once before `</body>` in both `base.html` and `base_public.html`. Wrap the
> whole thing in `{% if assistant_enabled %}`, and make that flag available to
> every template with
> `templates.env.globals["assistant_enabled"] = settings.ASSISTANT_ENABLED`
> in `main.py` — do not add it to the context of each route.
>
> The widget is a launcher button fixed bottom-right that opens a chat panel
> with a message log, six suggestion chips, a textarea and a send button.
> Enter sends, Shift+Enter makes a new line, Escape closes it. Show an
> animated typing indicator while waiting.
>
> **Styling** in a new `app/static/css/assistant.css`, and **behaviour** in a
> new `app/static/js/assistant.js`, both linked from the partial.
>
> Constraints:
>
> - No new frontend framework, no build step, no bundler, no npm. Plain
>   JavaScript in one file.
> - Reuse the CSS variables already declared in `app.css` (`--brand-navy`,
>   `--brand-gold`, `--surface`, `--border`, `--text-muted`, `--radius-lg`,
>   `--focus`) with sensible fallbacks. Do not invent a new palette and do not
>   edit `app.css`.
> - Accessible as built: a real `<button>` for the launcher with
>   `aria-expanded`, `aria-controls` and an `aria-label`; the log as
>   `role="log"` with `aria-live="polite"`; a label for the textarea; visible
>   focus styles; `prefers-reduced-motion` respected.
> - Works at phone width.
> - Add `httpx` to `requirements.txt`.
> - Do not modify any existing router, model, service or template other than
>   the two base templates. Do not reformat or reorder anything you touch.
>
> The assistant must never answer questions about an individual student —
> marks, attendance, dues. That rule lives in the n8n system prompt, not here,
> so do not try to enforce it in Python; just do not send anything that would
> let n8n identify who is asking. Put one line under the input saying that
> personal records are on the dashboard.
>
> When you are done, list every file you created or changed, and tell me the
> four lines I need to add to `.env`.

---

## Prompt 3 · The security clean-up

Run this one on its own, and read the diff before you accept it.

> In this repository, `.env` is tracked by git and contains `SECRET_KEY`, which
> signs the login cookies, and `sms.db` is tracked too. Fix both, carefully.
>
> 1. Add `.env` and `sms.db` to `.gitignore`.
> 2. Stop tracking them without deleting my local copies:
>    `git rm --cached .env sms.db`.
> 3. Create a root `.env.example` listing every setting name the application reads
>    (`APP_NAME`, `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_MINUTES`,
>    `ADMISSION_YEAR`, plus the four `ASSISTANT_*` settings:
>    `ASSISTANT_ENABLED`, `ASSISTANT_URL`, `ASSISTANT_KEY`, `ASSISTANT_TIMEOUT`)
>    with empty or placeholder values and a one-line comment each. No real values.
> 4. Tell me, in plain words, what I still have to do by hand: generate a new
>    `SECRET_KEY`, put it in my local `.env`, and understand that the old key
>    stays in the repository history, so rotating it is what actually protects
>    the application.
>
> Do not rewrite git history, do not force-push, and do not delete any file
> from my working directory. Show me the commands you ran and the diff.

---

## After the assistant finishes

Whatever it reports, check these four yourself. They take a minute and they are
the ones an assistant most often gets subtly wrong.

| Check | How |
|---|---|
| The key really is server-side | Browser dev tools → Network → ask a question. The request must go to `/assistant/ask` with no n8n address and no `x-college-key` header anywhere in it |
| The app still starts without n8n | Comment out `ASSISTANT_URL` in `.env`, restart. You should get a warning line and a working login page, not a traceback |
| Nothing else moved | `git diff --stat`. Five edited files, four new ones. If a router or a model appears in that list, ask why |
| The widget is on both shells | Check the login page and a role dashboard. Missing on the login page means `base_public.html` was skipped — the most common omission |
