import calendar
from datetime import date
import math
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.deps import require_role
from app.models.academics import Batch, Department, MentorGroup, Section, Student, Subject
from app.models.later import Attendance, LeaveRequest, Notice
from app.models.users import Role, User

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter(prefix="/student", tags=["Student"])


def _build_student_menu(active_url: str) -> list[dict]:
    # SA-01: Attendance menu item is enabled from Day 2
    return [
        {"label": "Dashboard", "url": "/student", "active": active_url == "/student"},
        {"label": "Attendance", "url": "/student/attendance", "active": active_url == "/student/attendance"},
        {"label": "Marks & Hall Ticket", "url": "#", "disabled": True, "tag": "Day 3"},
        {"label": "Leave Requests", "url": "#", "disabled": True, "tag": "Day 2"},
    ]


def _get_logged_in_student(session: Session, current_user: User) -> Student:
    student = session.exec(
        select(Student).where(Student.user_id == current_user.id)
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile record not found.",
        )
    return student


def _compute_overall_stats(records: list[Attendance]) -> dict:
    held = len(records)
    present_only = sum(1 for r in records if r.status == "present")
    late_count = sum(1 for r in records if r.status == "late")
    absent_count = sum(1 for r in records if r.status == "absent")
    # SA-03: Late counts as present
    attended = present_only + late_count
    pct = round((attended / held) * 100, 1) if held > 0 else 0.0
    is_safe = pct >= 75.0 if held > 0 else True

    can_miss = 0
    must_attend = 0
    if held > 0:
        if is_safe:
            # SA-07: Max additional periods m such that attended / (held + m) >= 0.75
            can_miss = max(0, math.floor((attended / 0.75) - held))
        else:
            # SA-08: Min consecutive periods x such that (attended + x) / (held + x) >= 0.75
            must_attend = max(1, math.ceil((0.75 * held - attended) / 0.25))

    return {
        "held": held,
        "present": present_only,
        "late": late_count,
        "absent": absent_count,
        "attended": attended,
        "pct": pct,
        "is_safe": is_safe,
        "can_miss": can_miss,
        "must_attend": must_attend,
    }


def _render_attendance_page(
    request: Request,
    current_user: User,
    student: Student,
    session: Session,
    selected_day_str: Optional[str] = None,
) -> HTMLResponse:
    department = session.get(Department, student.department_id)
    section = session.get(Section, student.section_id)

    records = session.exec(
        select(Attendance)
        .where(Attendance.student_id == student.id)
        .order_by(Attendance.date, Attendance.period)
    ).all()

    overall = _compute_overall_stats(records)

    # SA-09 & SA-10: Current semester subjects mapped to periods 1..6
    subjects = []
    if section:
        subjects = session.exec(
            select(Subject)
            .where(
                Subject.department_id == student.department_id,
                Subject.year == section.current_year,
                Subject.semester == section.current_semester,
            )
            .order_by(Subject.code)
        ).all()

    subject_by_period: dict[int, Subject] = {}
    for idx, sub in enumerate(subjects[:6], start=1):
        subject_by_period[idx] = sub

    subject_rows = []
    chart_labels = []
    chart_values = []
    chart_colors = []

    for period_num in range(1, 7):
        sub = subject_by_period.get(period_num)
        sub_records = [r for r in records if r.period == period_num]
        sub_held = len(sub_records)
        sub_attended = sum(1 for r in sub_records if r.status in ("present", "late"))
        sub_pct = round((sub_attended / sub_held) * 100, 1) if sub_held > 0 else 0.0
        sub_low = sub_held > 0 and sub_pct < 75.0

        code = sub.code if sub else f"P{period_num}"
        name = sub.name if sub else f"Period {period_num}"

        subject_rows.append(
            {
                "period": period_num,
                "code": code,
                "name": name,
                "held": sub_held,
                "attended": sub_attended,
                "pct": sub_pct,
                "is_low": sub_low,
            }
        )
        chart_labels.append(code)
        chart_values.append(sub_pct)
        chart_colors.append("#DC3545" if sub_low else "#0B2150")

    # SA-15: Approved leave requests for this student
    approved_leaves = session.exec(
        select(LeaveRequest).where(
            LeaveRequest.student_id == student.id,
            LeaveRequest.status == "approved",
        )
    ).all()

    def _is_approved_leave(d: date) -> bool:
        return any(lv.from_date <= d <= lv.to_date for lv in approved_leaves)

    # Group attendance records by date
    records_by_date: dict[date, list[Attendance]] = {}
    for r in records:
        records_by_date.setdefault(r.date, []).append(r)

    today = date.today()
    cal = calendar.Calendar(firstweekday=6)  # Sunday first column
    month_weeks = cal.monthdatescalendar(today.year, today.month)
    month_name = f"{calendar.month_name[today.month]} {today.year}"

    day_details_map: dict[str, dict] = {}
    calendar_weeks = []

    for week in month_weeks:
        week_cells = []
        for d in week:
            in_month = d.month == today.month
            iso = d.isoformat()
            day_recs = records_by_date.get(d, [])
            on_leave = _is_approved_leave(d)

            if not in_month:
                color = "outside"
            elif d.weekday() == 6 or (not day_recs and not on_leave):
                color = "grey"
            elif on_leave:
                color = "red"
            else:
                attended_cnt = sum(1 for r in day_recs if r.status in ("present", "late"))
                if attended_cnt == len(day_recs):
                    color = "green"
                elif attended_cnt == 0:
                    color = "red"
                else:
                    color = "amber"

            period_items = []
            rec_by_p = {r.period: r for r in day_recs}
            for p_num in range(1, 7):
                sub = subject_by_period.get(p_num)
                rec = rec_by_p.get(p_num)
                if rec:
                    st_label = rec.status.capitalize()
                elif on_leave:
                    st_label = "Absent (Leave)"
                else:
                    st_label = "No class"

                period_items.append(
                    {
                        "period": p_num,
                        "subject_code": sub.code if sub else f"P{p_num}",
                        "subject_name": sub.name if sub else f"Period {p_num}",
                        "status": st_label,
                    }
                )

            day_info = {
                "date_str": iso,
                "display_date": d.strftime("%d %b %Y (%a)"),
                "day_num": d.day,
                "in_month": in_month,
                "color": color,
                "on_leave": on_leave,
                "has_data": bool(day_recs) or on_leave,
                "periods": period_items,
            }
            if in_month:
                day_details_map[iso] = day_info
            week_cells.append(day_info)
        calendar_weeks.append(week_cells)

    # Default selected day: requested day, or most recent day with records
    default_day_str = None
    if selected_day_str and selected_day_str in day_details_map:
        default_day_str = selected_day_str
    elif records:
        latest_date_iso = max(records_by_date.keys()).isoformat()
        if latest_date_iso in day_details_map:
            default_day_str = latest_date_iso
    if not default_day_str:
        default_day_str = today.isoformat()

    return templates.TemplateResponse(
        request=request,
        name="student/attendance.html",
        context={
            "page_title": "My Attendance",
            "current_user": current_user,
            "menu_items": _build_student_menu("/student/attendance"),
            "student": student,
            "department": department,
            "section": section,
            "overall": overall,
            "subject_rows": subject_rows,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
            "chart_colors": chart_colors,
            "month_name": month_name,
            "calendar_weeks": calendar_weeks,
            "day_details_map": day_details_map,
            "default_day_str": default_day_str,
        },
    )


@router.get("", response_class=HTMLResponse)
def student_dashboard(
    request: Request,
    current_user: User = Depends(require_role(Role.student)),
    session: Session = Depends(get_session),
):
    student = session.exec(
        select(Student).where(Student.user_id == current_user.id)
    ).first()

    department = session.get(Department, student.department_id) if student else None
    batch = session.get(Batch, student.batch_id) if student else None
    section = session.get(Section, student.section_id) if student else None
    mentor_group = (
        session.get(MentorGroup, student.mentor_group_id)
        if student and student.mentor_group_id
        else None
    )
    mentor_user = (
        session.get(User, mentor_group.mentor_user_id)
        if mentor_group
        else None
    )

    # SA-18: Live overall attendance percentage for dashboard KPI card
    attendance_stats = None
    if student:
        att_records = session.exec(
            select(Attendance).where(Attendance.student_id == student.id)
        ).all()
        attendance_stats = _compute_overall_stats(att_records)

    latest_notice = session.exec(
        select(Notice).order_by(Notice.id.desc())
    ).first()

    raw_first = (student.full_name if student else current_user.full_name).split()[0]

    return templates.TemplateResponse(
        request=request,
        name="student/dashboard.html",
        context={
            "page_title": "Student Portal",
            "current_user": current_user,
            "menu_items": _build_student_menu("/student"),
            "first_name": raw_first,
            "student": student,
            "department": department,
            "batch": batch,
            "section": section,
            "mentor_group": mentor_group,
            "mentor_user": mentor_user,
            "attendance_stats": attendance_stats,
            "latest_notice": latest_notice,
        },
    )


@router.get("/attendance", response_class=HTMLResponse)
def student_attendance_view(
    request: Request,
    day: Optional[str] = None,
    current_user: User = Depends(require_role(Role.student)),
    session: Session = Depends(get_session),
):
    student = _get_logged_in_student(session, current_user)
    return _render_attendance_page(request, current_user, student, session, selected_day_str=day)


# SA-16: Prevent viewing another student's attendance by ID in URL
@router.get("/{target_student_id}/attendance", response_class=HTMLResponse)
def student_other_attendance_guard(
    target_student_id: int,
    request: Request,
    day: Optional[str] = None,
    current_user: User = Depends(require_role(Role.student)),
    session: Session = Depends(get_session),
):
    student = _get_logged_in_student(session, current_user)
    if target_student_id != student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view another student's attendance.",
        )
    return _render_attendance_page(request, current_user, student, session, selected_day_str=day)