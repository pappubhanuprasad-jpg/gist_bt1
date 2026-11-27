"""Manual end-to-end check for the public registration flow (run against a live server)."""

import io
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = "http://127.0.0.1:8010"
DB = os.path.join(os.path.dirname(__file__), "sms.db")
UPLOADS = os.path.join(os.path.dirname(__file__), "app", "static", "uploads", "registrations")

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"PASS  {label}")
    else:
        failures.append(label)
        print(f"FAIL  {label} {detail}")


def multipart(fields, files):
    boundary = "----sms" + uuid.uuid4().hex
    body = io.BytesIO()
    for key, value in fields.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        body.write(str(value).encode())
        body.write(b"\r\n")
    for key, (filename, content, content_type) in files.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(
            f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
        )
        body.write(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.write(content)
        body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())
    return body.getvalue(), f"multipart/form-data; boundary={boundary}"


def request(path, data=None, headers=None, follow=True):
    req = urllib.request.Request(BASE + path, data=data, headers=headers or {})
    opener = urllib.request.build_opener()
    if not follow:
        opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read().decode("utf-8", "replace")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


VALID_FIELDS = {
    "full_name": "Test Student",
    "dob": "2005-05-10",
    "gender": "Male",
    "phone": "9876543210",
    "email": "test.student@example.com",
    "parent_name": "Test Parent",
    "department_id": "1",
    "quota": "convener",
    "entrance_rank": "1234",
    "tenth_percent": "92.5",
    "inter_percent": "89.4",
}


def valid_files():
    return {
        "photo": ("photo.png", b"\x89PNG\r\n\x1a\n" + b"0" * 1024, "image/png"),
        "marks_memo": ("memo.pdf", b"%PDF-1.4\n" + b"0" * 2048, "application/pdf"),
        "id_proof": ("id.jpg", b"\xff\xd8\xff\xe0" + b"0" * 1024, "image/jpeg"),
    }


# Wait for the server to come up.
for _ in range(40):
    try:
        status, _, _ = request("/health")
        if status == 200:
            break
    except Exception:
        time.sleep(0.25)
else:
    sys.exit("server did not start")

# 1. GET form
status, _, html = request("/register")
check("GET /register returns 200", status == 200)
for label in ("Personal Details", "Academic Details", "Documents", "Review &amp; Submit"):
    check(f"form contains step '{label}'", label in html)
check("branch dropdown lists departments", "Computer Science and Engineering" in html)

# 2. Submit valid form
body, ctype = multipart(VALID_FIELDS, valid_files())
status, headers, _ = request("/register", data=body, headers={"Content-Type": ctype}, follow=False)
location = headers.get("Location", "")
check("valid POST returns 303", status == 303, f"got {status}")
check("redirects to done page", location == "/register/done/REG-2026-00001", location)

# 3. Done page
status, _, html = request("/register/done/REG-2026-00001")
check("done page 200", status == 200)
check("done page shows reference", "REG-2026-00001" in html)
check("done page shows save message", "Save this number to track your application" in html)

# 4. DB row and files
conn = sqlite3.connect(DB)
row = conn.execute(
    "select reference_no, full_name, phone, status, photo_path, marks_memo_path, id_proof_path "
    "from registrations where reference_no = ?",
    ("REG-2026-00001",),
).fetchone()
check("registration row exists", row is not None)
if row:
    check("status is pending", row[3] == "pending", row[3])
    check("phone saved", row[2] == "9876543210", row[2])
    check("photo path saved", row[4] == "/static/uploads/registrations/REG-2026-00001/photo.png", row[4])

folder = os.path.join(UPLOADS, "REG-2026-00001")
check("upload folder created", os.path.isdir(folder), folder)
if os.path.isdir(folder):
    saved = sorted(os.listdir(folder))
    check("three uploads saved", saved == ["id_proof.jpg", "marks_memo.pdf", "photo.png"], saved)

# 5. Status page
status, _, html = request("/register/status?ref=REG-2026-00001")
check("status page 200", status == 200)
check("status shows submitted step", "Submitted" in html)
check("status shows HOD step", "With CSE HOD" in html)
check("status shows pending", "Pending with CSE HOD" in html)

# 6. Oversized file -> clear error
big = b"0" * (5 * 1024 * 1024)
files = valid_files()
files["photo"] = ("huge.png", big, "image/png")
body, ctype = multipart(VALID_FIELDS, files)
status, _, html = request("/register", data=body, headers={"Content-Type": ctype}, follow=False)
check("5 MB upload rejected with 400", status == 400, f"got {status}")
check("5 MB error message shown", "exceeds the 2 MB limit" in html)

# 7. Bad extension -> clear error
files = valid_files()
files["marks_memo"] = ("memo.txt", b"hello", "text/plain")
body, ctype = multipart(VALID_FIELDS, files)
status, _, html = request("/register", data=body, headers={"Content-Type": ctype}, follow=False)
check("bad extension rejected with 400", status == 400, f"got {status}")
check("bad extension error shown", "must be .jpg, .jpeg, .png, or .pdf" in html)

# 8. Invalid phone + underage
bad = dict(VALID_FIELDS)
bad["phone"] = "12345"
bad["dob"] = "2015-01-01"
body, ctype = multipart(bad, valid_files())
status, _, html = request("/register", data=body, headers={"Content-Type": ctype}, follow=False)
check("invalid phone rejected", status == 400 and "exactly 10 digits" in html)
check("underage rejected", "at least 16 years old" in html)

# 9. Correction flow (simulate HOD sending back)
conn.execute(
    "update registrations set status='correction', hod_remarks='Please fix the name' "
    "where reference_no='REG-2026-00001'"
)
conn.commit()
conn.close()

status, _, html = request("/register/status?ref=REG-2026-00001")
check("status shows sent back", "Sent Back for Correction" in html)
check("status shows HOD remarks", "Please fix the name" in html)
check("status offers edit link", "/register/edit/REG-2026-00001" in html)

status, _, html = request("/register/edit/REG-2026-00001")
check("edit form 200", status == 200)
check("edit form prefilled", "Test Student" in html)

fixed = dict(VALID_FIELDS)
fixed["full_name"] = "Test Student Corrected"
body, ctype = multipart(fixed, {})
status, headers, _ = request(
    "/register/edit/REG-2026-00001", data=body, headers={"Content-Type": ctype}, follow=False
)
check("edit resubmit redirects", status == 303, f"got {status}")
check("edit resubmit goes to status", headers.get("Location", "").startswith("/register/status?ref=REG-2026-00001"))

conn = sqlite3.connect(DB)
row = conn.execute(
    "select full_name, status from registrations where reference_no='REG-2026-00001'"
).fetchone()
check("edit saved new name", row[0] == "Test Student Corrected", row[0])
check("status back to pending", row[1] == "pending", row[1])
conn.close()

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("ALL CHECKS PASSED")
