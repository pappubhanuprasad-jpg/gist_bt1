from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, func, select

from app.database import get_session
from app.deps import require_role
from app.models.academics import Batch, Department, Section, Student
from app.models.registration import Registration, RegistrationStatus
from app.models.users import Role, User

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter(prefix="/management", tags=["Management"])


def _build_management_menu(active_url: str) -> list[dict]:
    return [
        {"label": "Dashboard", "url": "/management", "active": active_url == "/management"},
        {"label": "Admin", "url": "/admin", "active": False},
        {"label": "Exams & Results", "url": "#", "disabled": True, "tag": "Day 3"},
        {"label": "Notices", "url": "#", "disabled": True, "tag": "Day 3"},
    ]


@router.get("", response_class=HTMLResponse)
def management_dashboard(
    request: Request,
    current_user: User = Depends(require_role(Role.management)),
    session: Session = Depends(get_session),
):
    total_students = session.exec(select(func.count(Student.id))).one()
    total_departments = session.exec(select(func.count(Department.id))).one()
    pending_registrations = session.exec(
        select(func.count(Registration.id)).where(
            Registration.status == RegistrationStatus.pending
        )
    ).one()

    # Students per current year (1, 2, 3, 4)
    students_by_year: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
    year_rows = session.exec(
        select(Section.current_year, func.count(Student.id))
        .join(Student, Student.section_id == Section.id)
        .group_by(Section.current_year)
    ).all()
    for yr, cnt in year_rows:
        students_by_year[yr] = cnt

    # Department breakdown for bar chart and summary table
    departments = session.exec(select(Department).order_by(Department.code)).all()
    dept_rows = []
    chart_labels = []
    chart_counts = []

    for dept in departments:
        hod = session.get(User, dept.hod_user_id) if dept.hod_user_id else None
        stu_count = session.exec(
            select(func.count(Student.id)).where(Student.department_id == dept.id)
        ).one()
        pend_count = session.exec(
            select(func.count(Registration.id)).where(
                Registration.department_id == dept.id,
                Registration.status == RegistrationStatus.pending,
            )
        ).one()

        chart_labels.append(dept.code)
        chart_counts.append(stu_count)
        dept_rows.append(
            {
                "code": dept.code,
                "name": dept.name,
                "hod_name": hod.full_name if hod else "Unassigned",
                "student_count": stu_count,
                "pending_count": pend_count,
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="management/dashboard.html",
        context={
            "page_title": "Management Dashboard",
            "current_user": current_user,
            "menu_items": _build_management_menu("/management"),
            "total_students": total_students,
            "total_departments": total_departments,
            "pending_registrations": pending_registrations,
            "students_by_year": students_by_year,
            "dept_rows": dept_rows,
            "chart_labels": chart_labels,
            "chart_counts": chart_counts,
        },
    )