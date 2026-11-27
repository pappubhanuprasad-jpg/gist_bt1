# Testing Commands for GIST SMS (`GET` Routes) & n8n College Assistant (`POST`)

All commands below target **Windows PowerShell 5.1** and **`curl.exe`** from
the repository root (`c:\COlleg SMS`).

> **PowerShell 5.1 tip:** In Windows PowerShell, bare `curl` is an alias for
> `Invoke-WebRequest`, **not** real curl. Always type `curl.exe` when running
> curl flags (`-X`, `-H`, `-c`, `-b`, `-d`), and pass `-UseBasicParsing` to
> `Invoke-WebRequest`.

---

## 1. Automated Test Suites (Offline, No Server Needed)

```powershell
# Run all 23 GIST SMS unit/integration tests
.\venv\Scripts\python.exe -m unittest discover -s tests -v

# Run all 60 n8n Python Code node checks (including no-imports verification)
.\venv\Scripts\python.exe "N8n Bot\Project_Files\code\test_code_nodes.py"
```

---

## 2. Start the Local GIST SMS Server

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Keep this terminal running and open a second PowerShell window in `c:\COlleg SMS`
for the HTTP tests below.

---

## 3. Testing `GET` Functionality (GIST SMS Pages, Data Lookup, Static Assets & Widget)

### 3.1 Public `GET` Endpoints (No Login Required)

#### Using PowerShell (`Invoke-RestMethod` / `Invoke-WebRequest`)

```powershell
# 1. Health check (JSON: {"status":"ok"})
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/health"

# 2. Root redirect (/ -> 302 to /login)
curl.exe -i http://127.0.0.1:8000/

# 3. Public pages (should all return 200 OK)
foreach ($path in @(
    "/login",
    "/register",
    "/register/done/REG-2026-00001",
    "/register/status",
    "/register/status?reference_no=REG-2026-00001",
    "/register/status/edit/REG-2026-00007"
)) {
    $res = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000$path"
    "{0,-45} -> HTTP {1}" -f $path, $res.StatusCode
}
```

#### Using `curl.exe`

```powershell
# Health check JSON
curl.exe -s http://127.0.0.1:8000/health

# Check status codes across public GET endpoints
foreach ($path in @("/health","/login","/register","/register/done/REG-2026-00001","/register/status?reference_no=REG-2026-00001","/register/status/edit/REG-2026-00007")) {
    $code = curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:8000$path"
    "$path -> HTTP $code"
}
```

> **Note on seeded IDs:** `REG-2026-00001` is a seeded `pending` application and
> `REG-2026-00007` is a seeded `correction` application in `sms.db`. If you
> re-seed (`.\venv\Scripts\python.exe -m scripts.seed`), those same IDs remain valid.

---

### 3.2 Verify Assistant Static Files & Widget HTML on `GET` Pages *(After Integration)*

Once you have copied the 4 files and updated `main.py`, `base.html`, and `base_public.html`:

```powershell
# Static assistant CSS and JS must return 200 OK
(Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/static/css/assistant.css").StatusCode
(Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/static/js/assistant.js").StatusCode

# Verify the chat widget markup is rendered on public GET pages (/login and /register)
(Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/login").Content -match 'id="assistantLauncher"'
(Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/register").Content -match 'id="assistantLauncher"'
```

---

### 3.3 Authenticated `GET` Endpoints (Role Dashboards & HOD Screens)

Role routes require the `access_token` HttpOnly cookie from `POST /login`.
Unauthenticated requests redirect (`303`) to `/login`.

#### Check unauthenticated redirect (`303 -> /login`)

```powershell
curl.exe -i http://127.0.0.1:8000/student
```

#### Test authenticated `GET` routes with `curl.exe` (cookie jar)

```powershell
# 1. Student login -> GET /student (also verify assistant widget on dashboard)
curl.exe -s -c cookies.txt -X POST http://127.0.0.1:8000/login -d "username=26CSE001&password=Student@123"
curl.exe -s -o NUL -w "GET /student -> HTTP %{http_code}`n" -b cookies.txt http://127.0.0.1:8000/student
curl.exe -s -b cookies.txt http://127.0.0.1:8000/student | Select-String "assistantLauncher"

# Negative RBAC check: student opening /hod must return 403 Forbidden
curl.exe -s -o NUL -w "Student GET /hod -> HTTP %{http_code}`n" -b cookies.txt http://127.0.0.1:8000/hod

# Logout clears the cookie (303 -> /login)
curl.exe -s -o NUL -w "GET /logout -> HTTP %{http_code}`n" -b cookies.txt -c cookies.txt http://127.0.0.1:8000/logout
```

```powershell
# 2. HOD login -> GET /hod and HOD sub-routes
curl.exe -s -c cookies_hod.txt -X POST http://127.0.0.1:8000/login -d "username=hod.cse@college.edu&password=Hod@123"
foreach ($path in @("/hod","/hod/registrations","/hod/registrations?status=pending","/hod/registrations/1","/hod/students","/hod/mentor-groups","/hod/subjects","/hod/leave-requests")) {
    $code = curl.exe -s -o NUL -w "%{http_code}" -b cookies_hod.txt "http://127.0.0.1:8000$path"
    "$path -> HTTP $code"
}
```

```powershell
# 3. Management, Mentor, and Trainer dashboards
curl.exe -s -c cookies_mgmt.txt -X POST http://127.0.0.1:8000/login -d "username=management@college.edu&password=Admin@123"
curl.exe -s -o NUL -w "GET /management -> HTTP %{http_code}`n" -b cookies_mgmt.txt http://127.0.0.1:8000/management

curl.exe -s -c cookies_mentor.txt -X POST http://127.0.0.1:8000/login -d "username=mentor.cse.2026a@college.edu&password=Mentor@123"
curl.exe -s -o NUL -w "GET /mentor -> HTTP %{http_code}`n" -b cookies_mentor.txt http://127.0.0.1:8000/mentor

curl.exe -s -c cookies_trainer.txt -X POST http://127.0.0.1:8000/login -d "username=trainer1@college.edu&password=Trainer@123"
curl.exe -s -o NUL -w "GET /trainer -> HTTP %{http_code}`n" -b cookies_trainer.txt http://127.0.0.1:8000/trainer

# Clean up temporary cookie jars
Remove-Item cookies*.txt -ErrorAction SilentlyContinue
```

#### Test authenticated `GET` routes with pure PowerShell (`-SessionVariable`)

```powershell
# Login and capture session cookies (Invoke-WebRequest follows 303 -> /student)
$studentPage = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "http://127.0.0.1:8000/login" -Body @{
    username = "26CSE001"
    password = "Student@123"
} -SessionVariable smsSession

"Login landed with HTTP $($studentPage.StatusCode), has Ravi Kumar: $($studentPage.Content -match 'Ravi Kumar')"

# Reuse $smsSession for subsequent GET requests
$studentGet = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/student" -WebSession $smsSession
"GET /student -> HTTP $($studentGet.StatusCode), has widget: $($studentGet.Content -match 'assistantLauncher')"
```

#### SQLADMIN `GET` endpoints (separate `/admin` session)

```powershell
# Unauthenticated /admin/ redirects to /admin/login (302)
curl.exe -i http://127.0.0.1:8000/admin/ | Select-String "HTTP/|Location:"

# Admin login page (200)
curl.exe -s -o NUL -w "GET /admin/login -> HTTP %{http_code}`n" http://127.0.0.1:8000/admin/login

# Sign in to /admin and test /admin/department/list
curl.exe -s -c cookies_admin.txt -X POST http://127.0.0.1:8000/admin/login -d "username=management@college.edu&password=Admin@123"
curl.exe -s -o NUL -w "GET /admin/ -> HTTP %{http_code}`n" -b cookies_admin.txt http://127.0.0.1:8000/admin/
curl.exe -s -o NUL -w "GET /admin/department/list -> HTTP %{http_code}`n" -b cookies_admin.txt http://127.0.0.1:8000/admin/department/list
Remove-Item cookies_admin.txt -ErrorAction SilentlyContinue
```

---

## 4. Testing the Chatbot Endpoint (`POST /assistant/ask` & n8n Webhook)

> **Important:** Neither FastAPI's `/assistant/ask` nor n8n's `/webhook/college-ask`
> exposes a `GET` endpoint — both are **`POST`-only**.
> Sending `GET http://127.0.0.1:8000/assistant/ask` returns `405 Method Not Allowed`.

### 4.1 Test via GIST SMS Proxy (`POST http://127.0.0.1:8000/assistant/ask`)

```powershell
# PowerShell (captures the assistant_sid cookie for multi-turn memory)
$resp = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/assistant/ask" `
  -ContentType "application/json" `
  -SessionVariable botSession `
  -Body '{"question":"What is the fee structure for B.Tech?"}'
$resp

# Follow-up question reusing the same conversation cookie
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/assistant/ask" `
  -ContentType "application/json" `
  -WebSession $botSession `
  -Body '{"question":"And what are the hostel charges?"}'

# Refusal / privacy boundary check (must not reveal personal marks)
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/assistant/ask" `
  -ContentType "application/json" `
  -WebSession $botSession `
  -Body '{"question":"What are my marks in the last mid exam?"}'
```

Using `curl.exe` (piping JSON via `-d "@-"` avoids Windows PowerShell 5.1 quote-splitting on spaces):

```powershell
'{"question":"What is the intake for CSE?"}' | curl.exe -s -X POST "http://127.0.0.1:8000/assistant/ask" `
  -H "Content-Type: application/json" `
  -c bot_cookies.txt `
  -d "@-"
Remove-Item bot_cookies.txt -ErrorAction SilentlyContinue
```

### 4.2 Test the n8n Ask Webhook Directly (Before or Without FastAPI)

> **Important on n8n Cloud + Windows PowerShell 5.1:** Cloudflare in front of
> `*.app.n8n.cloud` blocks `Invoke-RestMethod`'s default `WindowsPowerShell`
> `User-Agent` with `(403) Forbidden`. Use `curl.exe` (piping JSON via `-d "@-"`)
> for direct n8n Cloud calls. (`Invoke-RestMethod` still works fine against
> local `http://127.0.0.1:8000`.)

For the **Test URL** (click **Execute workflow** in n8n right before running; valid for 1 request):

```powershell
'{"question":"What is the fee for B.Tech?","session_id":"test-1"}' | curl.exe -s -X POST "https://your-instance.app.n8n.cloud/webhook-test/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"
```

For the **Production URL** (workflow must be **Published / Active** and Stage 1 ingested):

```powershell
'{"question":"What is the fee for B.Tech?","session_id":"test-1"}' | curl.exe -s -X POST "https://your-instance.app.n8n.cloud/webhook/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"
```

---

## 5. Stage 2 · Web Front Door (n8n Workflow Build & Verification Commands)

Follow these commands when building and testing **Stage 2** from
`Day4_College_Assistant_Build_Guide.docx` (before or alongside GIST SMS integration).

> **Before running Stage 2 tests:**
> 1. Run `.\venv\Scripts\python.exe "N8n Bot\Project_Files\code\test_code_nodes.py"` (60 offline node checks).
> 2. In n8n, run **Stage 1 (`Start Ingest`)** once so `Store Handbook` inserts the 11 handbook sections into `college_handbook`.
> 3. **Use `curl.exe --data "@-"` for `*.app.n8n.cloud`:** PowerShell 5.1's `Invoke-RestMethod` triggers a Cloudflare `403 Forbidden` on `*.app.n8n.cloud`, and inline `\"` JSON splits on spaces. Piping JSON to `curl.exe --data "@-"` avoids both issues.

### 5.1 Smoke Test (While Building — Test URL, Click "Execute workflow" First)

```powershell
'{"question":"What is the fee for B.Tech?","session_id":"test-1"}' | curl.exe -s -X POST "https://your-instance.app.n8n.cloud/webhook-test/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"
```

*(Once **Published / Active**, replace `/webhook-test/college-ask` with `/webhook/college-ask` in any command below. If you get `404 The requested webhook "college-ask" is not registered`, either click **Execute workflow** first for `/webhook-test/...`, or switch to `/webhook/...` if the workflow is already Published.)*

Expected JSON: `ok: true`, `answer` naming **48,000** (convener quota) and **85,000** (management quota) separately, and `source: "College handbook (sample data)"`.

### 5.2 Test `Parse Question` → `Reject Reply` Branch (AI Agent Must NOT Run)

```powershell
# Greeting bypass (uses Production URL; swap to /webhook-test/college-ask while unpublished)
'{"question":"hi","session_id":"reject-check"}' | curl.exe -s -X POST "https://your-instance.app.n8n.cloud/webhook/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"

# Too short (< 3 chars)
'{"question":"ok","session_id":"reject-check"}' | curl.exe -s -X POST "https://your-instance.app.n8n.cloud/webhook/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"

# Empty question
'{"question":"","session_id":"reject-check"}' | curl.exe -s -X POST "https://your-instance.app.n8n.cloud/webhook/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"
```

Check n8n **Executions**: `Question OK?` must take the `false` branch to `Reject Reply`, and `College Assistant (Web)` must show **no execution**.

### 5.3 Test `Chat Memory` (`session_id` Context Window)

```powershell
# Turn 1
'{"question":"What is the hostel fee?","session_id":"mem-check-1"}' | curl.exe -s -X POST "https://your-instance.app.n8n.cloud/webhook/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"

# Turn 2 (depends on Turn 1 via session_id = "mem-check-1")
'{"question":"And the bus?","session_id":"mem-check-1"}' | curl.exe -s -X POST "https://your-instance.app.n8n.cloud/webhook/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"
```

Expected: the second reply answers with GIST's **transport / bus fees (14,000 to 24,000 rupees per year)**, not generic bus information.

### 5.4 Run Full `Test_Questions.txt` Accuracy, Refusal & Multilingual Checks

*(Requires Published workflow at the Production URL.)*

```powershell
foreach ($q in @(
    "What is the fee for B.Tech?",
    "What is the sanctioned intake for CSE?",
    "What documents do I bring at registration?",
    "What is the minimum attendance?",
    "Who is the Head of the CSE department?",
    "What do the hostel and the bus cost?",
    "What are my marks in the last mid exam?",
    "Can you tell me my attendance percentage?",
    "Will I get a seat in CSE if my rank is 12,000?",
    "What is the Wi-Fi password?",
    "Is this college better than the one in Nellore?",
    "Are these fees official?",
    "I joined by lateral entry and want a hostel room. What do I pay?",
    "Fee entha?"
)) {
    $json = @{ question = $q; session_id = "qa-suite-1" } | ConvertTo-Json -Compress
    $res = ($json | curl.exe -s -X POST "https://your-instance.app.n8n.cloud/webhook/college-ask" `
      -H "Content-Type: application/json" `
      -H "x-college-key: YOUR_KEY" `
      --data "@-") | ConvertFrom-Json
    Write-Output "`nQ: $q"
    Write-Output "A: $($res.answer)"
}
```

### 5.5 Verify Webhook Auth (`401`/`403`), Inactive (`404`), and CORS (`OPTIONS`)

```powershell
# 1. Wrong key -> should return HTTP 401 or 403
'{"question":"What is the CSE intake?","session_id":"auth-test"}' | curl.exe -s -o NUL -w "Wrong key -> HTTP %{http_code}`n" `
  -X POST "https://your-instance.app.n8n.cloud/webhook/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: WRONG_KEY" `
  --data "@-"

# 2. Missing key -> should return HTTP 401 or 403
'{"question":"What is the CSE intake?","session_id":"auth-test"}' | curl.exe -s -o NUL -w "Missing key -> HTTP %{http_code}`n" `
  -X POST "https://your-instance.app.n8n.cloud/webhook/college-ask" `
  -H "Content-Type: application/json" `
  --data "@-"

# 3. CORS preflight check (only while Allowed Origins = * is set for standalone web/index.html)
curl.exe -s -i -X OPTIONS "https://your-instance.app.n8n.cloud/webhook/college-ask" `
  -H "Origin: http://localhost:8080" `
  -H "Access-Control-Request-Method: POST" `
  -H "Access-Control-Request-Headers: content-type,x-college-key" | Select-String "HTTP/|Access-Control-"
```

### 5.6 Test with Standalone `web/index.html` (Stage 2 Local Page)

```powershell
# Start static HTTP server for N8n Bot\Project_Files\web
.\venv\Scripts\python.exe -m http.server 8080 --directory "N8n Bot\Project_Files\web"
```

Open `http://localhost:8080` in a browser, enter your **Production URL** and **`x-college-key`** in the Connection panel, and test the suggestion chips. (Once integrated into GIST SMS, stop using `web/index.html` and remove `Allowed Origins (CORS)` from the **Ask Webhook** node in n8n.)

---

## 6. Stage 3 · Testing Telegram Update Payloads (`05_parse_telegram.py`)

`05_parse_telegram.py` (`Parse Telegram Message`) expects a **Telegram update**
JSON structure (`message` / `edited_message` / `channel_post` / `text` / `caption`
with `chat.id` and `from.first_name`), **not** `{"question": ..., "session_id": ...}`.

> **Important n8n Webhook note:** `05_parse_telegram.py` reads `root = item["json"]`
> directly (the format produced by **Telegram Trigger**), whereas an n8n
> **Webhook** node places the HTTP POST JSON under `item["json"]["body"]`.
> - If you test `05_parse_telegram.py` by sending HTTP POST requests to a Webhook
>   URL **without** changing Python code, place an n8n **Edit Fields (Set)** node
>   (or `{{ $json.body }}`) between the Webhook node and `Parse Telegram Message`,
>   or test using the Telegram bot / n8n Pin Data directly.
> - For the standard **Stage 2 POST Web Workflow** (`Ask Webhook`), connect
>   `Ask Webhook` → `Parse Question` (`02_parse_question.py`).

### 6.1 Standard Telegram Update Payload (`message.text`)

```powershell
'{"update_id":1,"message":{"text":"What is the fee for B.Tech?","chat":{"id":12345},"from":{"first_name":"Ravi"}}}' | curl.exe -i -X POST "https://your-instance.app.n8n.cloud/webhook-test/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"
```

### 6.2 Flat Message Payload (`text` + `chat` at root)

```powershell
'{"text":"What is the intake for CSE?","chat":{"id":12345},"from":{"first_name":"Ravi"}}' | curl.exe -i -X POST "https://your-instance.app.n8n.cloud/webhook-test/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"
```

### 6.3 Caption Payload (`message.caption`) & Opener (`/start`)

```powershell
# Photo/forward caption parsed as question
'{"update_id":2,"message":{"caption":"What is the hostel fee?","chat":{"id":12345},"from":{"first_name":"Ravi"}}}' | curl.exe -i -X POST "https://your-instance.app.n8n.cloud/webhook-test/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"

# /start opener -> routes to Telegram Welcome (Agent does not run)
'{"update_id":3,"message":{"text":"/start","chat":{"id":12345},"from":{"first_name":"Ravi"}}}' | curl.exe -i -X POST "https://your-instance.app.n8n.cloud/webhook-test/college-ask" `
  -H "Content-Type: application/json" `
  -H "x-college-key: YOUR_KEY" `
  --data "@-"
```

*(Once Published / Active, replace `/webhook-test/college-ask` with `/webhook/college-ask`.)*
