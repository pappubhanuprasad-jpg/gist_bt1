from datetime import date
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, func, select

from app.config import settings
from app.database import get_session
from app.models.academics import Department, Student
from app.models.registration import Registration, RegistrationStatus

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_BASE = BASE_DIR / "static" / "uploads" / "registrations"
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter(prefix="/register", tags=["Public Registration"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


def _calculate_age(dob: date, today: date) -> int:
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _generate_reference_no(session: Session) -> str:
    max_id = session.exec(select(func.max(Registration.id))).one()
    next_num = (max_id or 0) + 1
    return f"REG-{settings.ADMISSION_YEAR}-{next_num:05d}"


async def _validate_upload(upload: UploadFile, label: str) -> tuple[Optional[bytes], Optional[str]]:
    if not upload or not upload.filename:
        return None, f"{label} is required."

    ext = Path(upload.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None, f"{label} must be .jpg, .jpeg, .png, or .pdf (got '{ext or 'unknown'}')."

    content = await upload.read()
    if len(content) == 0:
        return None, f"{label} cannot be empty."
    if len(content) > MAX_FILE_SIZE:
        size_mb = len(content) / (1024 * 1024)
        return None, f"{label} exceeds the 2 MB limit ({size_mb:.2f} MB uploaded)."

    return content, None


def _save_upload_file(ref_no: str, field_name: str, original_filename: str, content: bytes) -> str:
    ext = Path(original_filename).suffix.lower()
    target_dir = UPLOADS_BASE / ref_no
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{field_name}{ext}"
    file_path.write_bytes(content)
    return f"/static/uploads/registrations/{ref_no}/{field_name}{ext}"


def _validate_registration_fields(
    full_name: str,
    dob_str: str,
    gender: str,
    phone: str,
    email: str,
    parent_name: str,
    department_id: int,
    quota: str,
    entrance_rank_str: str,
    tenth_percent: float,
    inter_percent: float,
    session: Session,
) -> tuple[Optional[dict], list[str]]:
    errors: list[str] = []

    if not full_name.strip():
        errors.append("Full name is required.")
    if not gender.strip():
        errors.append("Gender is required.")
    if not parent_name.strip():
        errors.append("Parent/Guardian name is required.")
    if not email.strip() or "@" not in email:
        errors.append("A valid email address is required.")

    cleaned_phone = phone.strip()
    if not (cleaned_phone.isdigit() and len(cleaned_phone) == 10):
        errors.append("Phone number must be exactly 10 digits.")

    parsed_dob: Optional[date] = None
    try:
        parsed_dob = date.fromisoformat(dob_str)
        if _calculate_age(parsed_dob, date.today()) < 16:
            errors.append("Applicant must be at least 16 years old.")
    except ValueError:
        errors.append("Please enter a valid Date of Birth.")

    dept = session.get(Department, department_id)
    if not dept:
        errors.append("Please select a valid B.Tech branch.")

    if quota not in {"convener", "management", "spot"}:
        errors.append("Please select a valid admission quota.")

    entrance_rank: Optional[int] = None
    if entrance_rank_str and entrance_rank_str.strip():
        try:
            entrance_rank = int(entrance_rank_str.strip())
            if entrance_rank <= 0:
                errors.append("Entrance rank must be a positive number.")
        except ValueError:
            errors.append("Entrance rank must be a valid integer.")

    if not (0.0 <= tenth_percent <= 100.0):
        errors.append("10th percentage must be between 0 and 100.")
    if not (0.0 <= inter_percent <= 100.0):
        errors.append("Intermediate / 12th percentage must be between 0 and 100.")

    if errors:
        return None, errors

    return {
        "full_name": full_name.strip(),
        "dob": parsed_dob,
        "gender": gender.strip(),
        "phone": cleaned_phone,
        "email": email.strip(),
        "parent_name": parent_name.strip(),
        "department_id": department_id,
        "quota": quota,
        "entrance_rank": entrance_rank,
        "tenth_percent": round(tenth_percent, 2),
        "inter_percent": round(inter_percent, 2),
    }, []


@router.get("", response_class=HTMLResponse)
def register_form_page(
    request: Request,
    session: Session = Depends(get_session),
):
    departments = session.exec(select(Department).order_by(Department.code)).all()
    return templates.TemplateResponse(
        request=request,
        name="register/form.html",
        context={
            "page_title": "First-Year B.Tech Registration",
            "departments": departments,
            "errors": [],
            "form_data": {},
        },
    )


@router.post("", response_class=HTMLResponse)
async def register_form_submit(
    request: Request,
    full_name: str = Form(""),
    dob: str = Form(""),
    gender: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    parent_name: str = Form(""),
    department_id: int = Form(0),
    quota: str = Form(""),
    entrance_rank: str = Form(""),
    tenth_percent: float = Form(-1.0),
    inter_percent: float = Form(-1.0),
    photo: Optional[UploadFile] = File(None),
    marks_memo: Optional[UploadFile] = File(None),
    id_proof: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
):
    form_data = {
        "full_name": full_name,
        "dob": dob,
        "gender": gender,
        "phone": phone,
        "email": email,
        "parent_name": parent_name,
        "department_id": department_id,
        "quota": quota,
        "entrance_rank": entrance_rank,
        "tenth_percent": "" if tenth_percent < 0 else tenth_percent,
        "inter_percent": "" if inter_percent < 0 else inter_percent,
    }

    cleaned, errors = _validate_registration_fields(
        full_name=full_name,
        dob_str=dob,
        gender=gender,
        phone=phone,
        email=email,
        parent_name=parent_name,
        department_id=department_id,
        quota=quota,
        entrance_rank_str=entrance_rank,
        tenth_percent=tenth_percent,
        inter_percent=inter_percent,
        session=session,
    )

    photo_bytes, photo_err = await _validate_upload(photo, "Passport Photo")
    memo_bytes, memo_err = await _validate_upload(marks_memo, "Marks Memo")
    id_bytes, id_err = await _validate_upload(id_proof, "ID Proof")

    for err in (photo_err, memo_err, id_err):
        if err:
            errors.append(err)

    if errors or not cleaned:
        departments = session.exec(select(Department).order_by(Department.code)).all()
        return templates.TemplateResponse(
            request=request,
            name="register/form.html",
            context={
                "page_title": "First-Year B.Tech Registration",
                "departments": departments,
                "errors": errors,
                "form_data": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    ref_no = _generate_reference_no(session)

    photo_path = _save_upload_file(ref_no, "photo", photo.filename, photo_bytes)
    marks_memo_path = _save_upload_file(ref_no, "marks_memo", marks_memo.filename, memo_bytes)
    id_proof_path = _save_upload_file(ref_no, "id_proof", id_proof.filename, id_bytes)

    registration = Registration(
        reference_no=ref_no,
        full_name=cleaned["full_name"],
        dob=cleaned["dob"],
        gender=cleaned["gender"],
        phone=cleaned["phone"],
        email=cleaned["email"],
        parent_name=cleaned["parent_name"],
        department_id=cleaned["department_id"],
        quota=cleaned["quota"],
        entrance_rank=cleaned["entrance_rank"],
        tenth_percent=cleaned["tenth_percent"],
        inter_percent=cleaned["inter_percent"],
        photo_path=photo_path,
        marks_memo_path=marks_memo_path,
        id_proof_path=id_proof_path,
        status=RegistrationStatus.pending,
    )
    session.add(registration)
    session.commit()

    return RedirectResponse(
        url=f"/register/done/{ref_no}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/done/{reference_no}", response_class=HTMLResponse)
def register_done_page(
    reference_no: str,
    request: Request,
    session: Session = Depends(get_session),
):
    reg = session.exec(
        select(Registration).where(Registration.reference_no == reference_no.strip().upper())
    ).first()
    if not reg:
        return RedirectResponse(url="/register/status", status_code=status.HTTP_303_SEE_OTHER)

    dept = session.get(Department, reg.department_id)
    return templates.TemplateResponse(
        request=request,
        name="register/done.html",
        context={
            "page_title": "Registration Submitted",
            "registration": reg,
            "department": dept,
        },
    )


@router.get("/status", response_class=HTMLResponse)
def register_status_page(
    request: Request,
    ref: Optional[str] = None,
    updated: Optional[str] = None,
    session: Session = Depends(get_session),
):
    reg: Optional[Registration] = None
    dept: Optional[Department] = None
    student: Optional[Student] = None
    not_found = False

    cleaned_ref = ref.strip().upper() if ref else ""
    if cleaned_ref:
        reg = session.exec(
            select(Registration).where(Registration.reference_no == cleaned_ref)
        ).first()
        if not reg:
            not_found = True
        else:
            dept = session.get(Department, reg.department_id)
            if reg.student_id:
                student = session.get(Student, reg.student_id)

    return templates.TemplateResponse(
        request=request,
        name="register/status.html",
        context={
            "page_title": "Track Application Status",
            "ref_query": cleaned_ref,
            "registration": reg,
            "department": dept,
            "student": student,
            "not_found": not_found,
            "updated": updated == "1",
        },
    )


@router.get("/edit/{reference_no}", response_class=HTMLResponse)
def register_edit_page(
    reference_no: str,
    request: Request,
    session: Session = Depends(get_session),
):
    reg = session.exec(
        select(Registration).where(Registration.reference_no == reference_no.strip().upper())
    ).first()
    if not reg or reg.status != RegistrationStatus.correction:
        return RedirectResponse(
            url=f"/register/status?ref={reference_no.strip().upper()}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    departments = session.exec(select(Department).order_by(Department.code)).all()
    return templates.TemplateResponse(
        request=request,
        name="register/edit.html",
        context={
            "page_title": "Correct & Resubmit Application",
            "registration": reg,
            "departments": departments,
            "errors": [],
        },
    )


@router.post("/edit/{reference_no}", response_class=HTMLResponse)
async def register_edit_submit(
    reference_no: str,
    request: Request,
    full_name: str = Form(""),
    dob: str = Form(""),
    gender: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    parent_name: str = Form(""),
    department_id: int = Form(0),
    quota: str = Form(""),
    entrance_rank: str = Form(""),
    tenth_percent: float = Form(-1.0),
    inter_percent: float = Form(-1.0),
    photo: Optional[UploadFile] = File(None),
    marks_memo: Optional[UploadFile] = File(None),
    id_proof: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
):
    reg = session.exec(
        select(Registration).where(Registration.reference_no == reference_no.strip().upper())
    ).first()
    if not reg or reg.status != RegistrationStatus.correction:
        return RedirectResponse(
            url=f"/register/status?ref={reference_no.strip().upper()}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    cleaned, errors = _validate_registration_fields(
        full_name=full_name,
        dob_str=dob,
        gender=gender,
        phone=phone,
        email=email,
        parent_name=parent_name,
        department_id=department_id,
        quota=quota,
        entrance_rank_str=entrance_rank,
        tenth_percent=tenth_percent,
        inter_percent=inter_percent,
        session=session,
    )

    new_uploads: dict[str, tuple[str, bytes]] = {}
    for field_key, file_obj, label in [
        ("photo", photo, "Passport Photo"),
        ("marks_memo", marks_memo, "Marks Memo"),
        ("id_proof", id_proof, "ID Proof"),
    ]:
        if file_obj and file_obj.filename:
            content, err = await _validate_upload(file_obj, label)
            if err:
                errors.append(err)
            elif content:
                new_uploads[field_key] = (file_obj.filename, content)

    if errors or not cleaned:
        departments = session.exec(select(Department).order_by(Department.code)).all()
        return templates.TemplateResponse(
            request=request,
            name="register/edit.html",
            context={
                "page_title": "Correct & Resubmit Application",
                "registration": reg,
                "departments": departments,
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    reg.full_name = cleaned["full_name"]
    reg.dob = cleaned["dob"]
    reg.gender = cleaned["gender"]
    reg.phone = cleaned["phone"]
    reg.email = cleaned["email"]
    reg.parent_name = cleaned["parent_name"]
    reg.department_id = cleaned["department_id"]
    reg.quota = cleaned["quota"]
    reg.entrance_rank = cleaned["entrance_rank"]
    reg.tenth_percent = cleaned["tenth_percent"]
    reg.inter_percent = cleaned["inter_percent"]

    if "photo" in new_uploads:
        fname, data = new_uploads["photo"]
        reg.photo_path = _save_upload_file(reg.reference_no, "photo", fname, data)
    if "marks_memo" in new_uploads:
        fname, data = new_uploads["marks_memo"]
        reg.marks_memo_path = _save_upload_file(reg.reference_no, "marks_memo", fname, data)
    if "id_proof" in new_uploads:
        fname, data = new_uploads["id_proof"]
        reg.id_proof_path = _save_upload_file(reg.reference_no, "id_proof", fname, data)

    reg.status = RegistrationStatus.pending
    session.add(reg)
    session.commit()

    return RedirectResponse(
        url=f"/register/status?ref={reg.reference_no}&updated=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )