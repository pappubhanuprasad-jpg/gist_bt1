from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, func, select

from app.config import settings
from app.database import get_session
from app.deps import require_role
from app.models.academics import Batch, Department, MentorGroup, Section, Student
from app.models.registration import Registration, RegistrationStatus
from app.models.users import Role, User
from app.services.approval import approve_registration

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter(prefix="/hod", tags=["HOD"])


def _get_hod_department(session: Session, hod_user: User) -> Department:
    if not hod_user.department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No department assigned to this HOD account.",
        )
    dept = session.get(Department, hod_user.department_id)
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned department not found.",
        )
    return dept


def _build_hod_menu(session: Session, dept_id: int, active_url: str) -> list[dict]:
    pending_count = session.exec(
        select(func.count(Registration.id)).where(
            Registration.department_id == dept_id,
            Registration.status == RegistrationStatus.pending,
        )
    ).one()

    return [
        {"label": "Dashboard", "url": "/hod", "active": active_url == "/hod"},
        {
            "label": "Registrations",
            "url": "/hod/registrations",
            "active": active_url.startswith("/hod/registrations"),
            "badge": pending_count,
        },
        {"label": "Students", "url": "#", "disabled": True, "tag": "Day 2"},
        {"label": "Mentor groups", "url": "#", "disabled": True, "tag": "Day 2"},
        {"label": "Subjects", "url": "#", "disabled": True, "tag": "Day 2"},
        {"label": "Leave requests", "url": "#", "disabled": True, "tag": "Day 2"},
    ]


def _get_own_registration(session: Session, reg_id: int, dept_id: int) -> Registration:
    reg = session.get(Registration, reg_id)
    if not reg or reg.department_id != dept_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found in your department.",
        )
    return reg


@router.get("", response_class=HTMLResponse)
def hod_dashboard(
    request: Request,
    current_user: User = Depends(require_role(Role.hod)),
    session: Session = Depends(get_session),
):
    dept = _get_hod_department(session, current_user)
    menu_items = _build_hod_menu(session, dept.id, "/hod")

    # DB-09: Department-scoped KPI cards
    total_students = session.exec(
        select(func.count(Student.id)).where(Student.department_id == dept.id)
    ).one()

    sections = session.exec(
        select(Section, Batch)
        .join(Batch, Section.batch_id == Batch.id)
        .where(Batch.department_id == dept.id)
        .order_by(Batch.start_year.desc(), Section.name)
    ).all()

    total_sections = len(sections)

    total_mentor_groups = session.exec(
        select(func.count(MentorGroup.id))
        .join(Section, MentorGroup.section_id == Section.id)
        .join(Batch, Section.batch_id == Batch.id)
        .where(Batch.department_id == dept.id)
    ).one()

    pending_registrations = session.exec(
        select(func.count(Registration.id)).where(
            Registration.department_id == dept.id,
            Registration.status == RegistrationStatus.pending,
        )
    ).one()

    # DB-10 & DB-11: Sections with student counts, mentor names & unassigned student warning
    section_rows = []
    sections_with_unassigned: list[str] = []

    for sec, batch in sections:
        stu_count = session.exec(
            select(func.count(Student.id)).where(Student.section_id == sec.id)
        ).one()
        unassigned_count = session.exec(
            select(func.count(Student.id)).where(
                Student.section_id == sec.id,
                Student.mentor_group_id == None,  # noqa: E711
            )
        ).one()

        label = f"{dept.code}-{batch.start_year} Sec {sec.name}"
        if unassigned_count > 0:
            sections_with_unassigned.append(f"{label} ({unassigned_count} unassigned)")

        groups = session.exec(
            select(MentorGroup).where(MentorGroup.section_id == sec.id)
        ).all()
        mentor_names = []
        for g in groups:
            m_user = session.get(User, g.mentor_user_id)
            if m_user:
                mentor_names.append(m_user.full_name)

        section_rows.append(
            {
                "batch_label": f"{batch.start_year}–{batch.end_year}",
                "year_sem": f"Year {sec.current_year} / Sem {sec.current_semester}",
                "section_name": sec.name,
                "student_count": stu_count,
                "capacity": sec.capacity,
                "mentors": ", ".join(mentor_names) if mentor_names else "None assigned",
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="hod/dashboard.html",
        context={
            "page_title": f"{dept.code} Department Dashboard",
            "current_user": current_user,
            "menu_items": menu_items,
            "department": dept,
            "total_students": total_students,
            "total_sections": total_sections,
            "total_mentor_groups": total_mentor_groups,
            "pending_registrations": pending_registrations,
            "section_rows": section_rows,
            "sections_with_unassigned": sections_with_unassigned,
        },
    )


@router.get("/registrations", response_class=HTMLResponse)
def hod_registrations_list(
    request: Request,
    status_filter: str = "all",
    current_user: User = Depends(require_role(Role.hod)),
    session: Session = Depends(get_session),
):
    dept = _get_hod_department(session, current_user)
    menu_items = _build_hod_menu(session, dept.id, "/hod/registrations")

    pending_count = session.exec(
        select(func.count(Registration.id)).where(
            Registration.department_id == dept.id,
            Registration.status == RegistrationStatus.pending,
        )
    ).one()

    approved_this_year = session.exec(
        select(func.count(Student.id)).where(
            Student.department_id == dept.id,
            Student.admission_year == settings.ADMISSION_YEAR,
        )
    ).one()

    correction_count = session.exec(
        select(func.count(Registration.id)).where(
            Registration.department_id == dept.id,
            Registration.status == RegistrationStatus.correction,
        )
    ).one()

    rejected_count = session.exec(
        select(func.count(Registration.id)).where(
            Registration.department_id == dept.id,
            Registration.status == RegistrationStatus.rejected,
        )
    ).one()

    query = select(Registration).where(Registration.department_id == dept.id)
    valid_statuses = {s.value for s in RegistrationStatus}
    if status_filter in valid_statuses:
        query = query.where(Registration.status == RegistrationStatus(status_filter))

    registrations = session.exec(query.order_by(Registration.id.desc())).all()

    rows = []
    for r in registrations:
        docs_uploaded = sum(
            1 for p in (r.photo_path, r.marks_memo_path, r.id_proof_path) if p
        )
        rows.append({"reg": r, "docs_count": f"{docs_uploaded}/3"})

    return templates.TemplateResponse(
        request=request,
        name="hod/registrations.html",
        context={
            "page_title": f"{dept.code} — Student Registrations",
            "current_user": current_user,
            "menu_items": menu_items,
            "department": dept,
            "pending_count": pending_count,
            "approved_this_year": approved_this_year,
            "correction_count": correction_count,
            "rejected_count": rejected_count,
            "status_filter": status_filter,
            "rows": rows,
        },
    )


@router.get("/registrations/{reg_id}", response_class=HTMLResponse)
def hod_registration_detail(
    reg_id: int,
    request: Request,
    msg: Optional[str] = None,
    error: Optional[str] = None,
    current_user: User = Depends(require_role(Role.hod)),
    session: Session = Depends(get_session),
):
    dept = _get_hod_department(session, current_user)
    reg = _get_own_registration(session, reg_id, dept.id)
    menu_items = _build_hod_menu(session, dept.id, "/hod/registrations")

    student = session.get(Student, reg.student_id) if reg.student_id else None

    return templates.TemplateResponse(
        request=request,
        name="hod/registration_detail.html",
        context={
            "page_title": f"Application {reg.reference_no}",
            "current_user": current_user,
            "menu_items": menu_items,
            "department": dept,
            "reg": reg,
            "student": student,
            "msg": msg,
            "error": error,
        },
    )


@router.post("/registrations/{reg_id}/approve", response_class=HTMLResponse)
def hod_approve_registration(
    reg_id: int,
    request: Request,
    remarks: str = Form(""),
    current_user: User = Depends(require_role(Role.hod)),
    session: Session = Depends(get_session),
):
    dept = _get_hod_department(session, current_user)
    reg = _get_own_registration(session, reg_id, dept.id)

    if reg.status != RegistrationStatus.pending:
        menu_items = _build_hod_menu(session, dept.id, "/hod/registrations")
        student = session.get(Student, reg.student_id) if reg.student_id else None
        return templates.TemplateResponse(
            request=request,
            name="hod/registration_detail.html",
            context={
                "page_title": f"Application {reg.reference_no}",
                "current_user": current_user,
                "menu_items": menu_items,
                "department": dept,
                "reg": reg,
                "student": student,
                "msg": None,
                "error": f"This application cannot be approved because its status is already '{reg.status.value}'.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    outcome = approve_registration(
        session=session,
        registration=reg,
        hod_user=current_user,
        remarks=remarks,
    )

    menu_items = _build_hod_menu(session, dept.id, "/hod/registrations")
    return templates.TemplateResponse(
        request=request,
        name="hod/approved_result.html",
        context={
            "page_title": "Registration Approved",
            "current_user": current_user,
            "menu_items": menu_items,
            "outcome": outcome,
        },
    )


@router.post("/registrations/{reg_id}/reject", response_class=HTMLResponse)
def hod_reject_registration(
    reg_id: int,
    request: Request,
    remarks: str = Form(""),
    current_user: User = Depends(require_role(Role.hod)),
    session: Session = Depends(get_session),
):
    dept = _get_hod_department(session, current_user)
    reg = _get_own_registration(session, reg_id, dept.id)

    if reg.status != RegistrationStatus.pending:
        return RedirectResponse(
            url=f"/hod/registrations/{reg.id}?error=Application+is+no+longer+pending",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not remarks.strip():
        menu_items = _build_hod_menu(session, dept.id, "/hod/registrations")
        return templates.TemplateResponse(
            request=request,
            name="hod/registration_detail.html",
            context={
                "page_title": f"Application {reg.reference_no}",
                "current_user": current_user,
                "menu_items": menu_items,
                "department": dept,
                "reg": reg,
                "student": None,
                "msg": None,
                "error": "Remarks are required when rejecting an application.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    reg.status = RegistrationStatus.rejected
    reg.hod_remarks = remarks.strip()
    reg.decided_at = datetime.now(timezone.utc)
    reg.decided_by_user_id = current_user.id
    session.add(reg)
    session.commit()

    return RedirectResponse(
        url=f"/hod/registrations/{reg.id}?msg=Application+rejected",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/registrations/{reg_id}/correction", response_class=HTMLResponse)
def hod_correction_registration(
    reg_id: int,
    request: Request,
    remarks: str = Form(""),
    current_user: User = Depends(require_role(Role.hod)),
    session: Session = Depends(get_session),
):
    dept = _get_hod_department(session, current_user)
    reg = _get_own_registration(session, reg_id, dept.id)

    if reg.status != RegistrationStatus.pending:
        return RedirectResponse(
            url=f"/hod/registrations/{reg.id}?error=Application+is+no+longer+pending",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not remarks.strip():
        menu_items = _build_hod_menu(session, dept.id, "/hod/registrations")
        return templates.TemplateResponse(
            request=request,
            name="hod/registration_detail.html",
            context={
                "page_title": f"Application {reg.reference_no}",
                "current_user": current_user,
                "menu_items": menu_items,
                "department": dept,
                "reg": reg,
                "student": None,
                "msg": None,
                "error": "Remarks are required when sending an application back for correction.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    reg.status = RegistrationStatus.correction
    reg.hod_remarks = remarks.strip()
    reg.decided_at = datetime.now(timezone.utc)
    reg.decided_by_user_id = current_user.id
    session.add(reg)
    session.commit()

    return RedirectResponse(
        url=f"/hod/registrations/{reg.id}?msg=Application+sent+back+for+correction",
        status_code=status.HTTP_303_SEE_OTHER,
    )