from datetime import datetime, timezone
import secrets
import string
from sqlmodel import Session

from app.config import settings
from app.models.academics import Department, Student
from app.models.registration import Registration, RegistrationStatus
from app.models.users import Role, User
from app.security import hash_password
from app.services.placement import get_or_create_batch, pick_mentor_group, pick_section
from app.services.roll_number import next_roll_number


def _generate_temp_password(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def approve_registration(
    session: Session,
    registration: Registration,
    hod_user: User,
    remarks: str | None = None,
) -> dict:
    """
    Approve a pending registration in one atomic transaction:
    - Verifies registration is pending and belongs to hod_user's department.
    - Generates roll number, student User (8-char temp password, must_change_password=True),
      and Student record assigned to batch, section, and mentor group.
    - Updates registration status to approved, commits once, and rolls back on any failure.
    """
    try:
        if registration.status != RegistrationStatus.pending:
            raise ValueError(
                f"Cannot approve registration: status is already '{registration.status.value}'."
            )

        if hod_user.department_id != registration.department_id:
            raise PermissionError(
                "HOD department does not match the registration department."
            )

        department = session.get(Department, registration.department_id)
        if not department:
            raise ValueError("Department not found.")

        admission_year = settings.ADMISSION_YEAR
        roll_number = next_roll_number(session, department, admission_year)

        batch = get_or_create_batch(session, department, admission_year)
        section = pick_section(session, batch)
        mentor_group = pick_mentor_group(session, section)

        temp_password = _generate_temp_password(8)

        student_user = User(
            username=roll_number,
            full_name=registration.full_name,
            email=registration.email,
            password_hash=hash_password(temp_password),
            role=Role.student,
            department_id=department.id,
            is_active=True,
            must_change_password=True,
        )
        session.add(student_user)
        session.flush()

        student = Student(
            user_id=student_user.id,
            roll_number=roll_number,
            full_name=registration.full_name,
            dob=registration.dob,
            gender=registration.gender,
            phone=registration.phone,
            email=registration.email,
            parent_name=registration.parent_name,
            department_id=department.id,
            batch_id=batch.id,
            section_id=section.id,
            mentor_group_id=mentor_group.id if mentor_group else None,
            quota=registration.quota,
            admission_year=admission_year,
            status="active",
        )
        session.add(student)
        session.flush()

        registration.status = RegistrationStatus.approved
        registration.decided_at = datetime.now(timezone.utc)
        registration.decided_by_user_id = hod_user.id
        registration.student_id = student.id
        if remarks and remarks.strip():
            registration.hod_remarks = remarks.strip()
        session.add(registration)

        session.commit()
        session.refresh(student)

        mentor_user = (
            session.get(User, mentor_group.mentor_user_id)
            if mentor_group
            else None
        )

        return {
            "student": student,
            "department": department,
            "roll_number": roll_number,
            "username": roll_number,
            "temp_password": temp_password,
            "section_name": section.name,
            "mentor_group_name": mentor_group.name if mentor_group else None,
            "mentor_name": mentor_user.full_name if mentor_user else None,
            "mentor_warning": (
                None
                if mentor_group
                else "Create a new mentor group for this section"
            ),
            "year_part": f"{admission_year % 100:02d}",
            "branch_part": department.code.upper(),
            "serial_part": roll_number[-3:],
        }
    except Exception:
        session.rollback()
        raise