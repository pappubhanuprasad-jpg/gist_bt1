from dataclasses import dataclass
from datetime import datetime, timezone
import secrets
import string
from sqlmodel import Session, func, select

from app.config import settings
from app.models.academics import (
    Batch,
    Department,
    MentorGroup,
    RollCounter,
    Section,
    Student,
)
from app.models.registration import Registration, RegistrationStatus
from app.models.users import Role, User
from app.security import hash_password


@dataclass
class ApprovalOutcome:
    student: Student
    department: Department
    section: Section
    mentor_group: MentorGroup
    mentor_user: User
    username: str
    temp_password: str
    year_part: str
    branch_part: str
    serial_part: str


def _generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def approve_registration(
    session: Session,
    registration_id: int,
    hod_user: User,
    remarks: str | None = None,
) -> ApprovalOutcome:
    """
    Approve a pending registration inside the caller's database transaction:
    1. Generate roll number (YY + BRANCH + 3-digit serial, starting at 101).
    2. Create student User login (username = roll_number, temp password, must_change_password=True).
    3. Ensure Batch, Section (A/B, max 60), and MentorGroup (max 30) exist and assign the student.
    4. Create Student row and mark Registration approved.
    """
    reg = session.get(Registration, registration_id)
    if not reg:
        raise ValueError("Registration not found.")
    if reg.status != RegistrationStatus.pending:
        raise ValueError(f"Cannot approve registration because its status is '{reg.status.value}'.")
    if hod_user.department_id != reg.department_id:
        raise PermissionError("You can only approve registrations for your own department.")

    dept = session.get(Department, reg.department_id)
    if not dept:
        raise ValueError("Department not found.")

    admission_year = settings.ADMISSION_YEAR

    # 1. Increment RollCounter (starts at 100 so first student is 101)
    counter = session.exec(
        select(RollCounter).where(
            RollCounter.department_id == dept.id,
            RollCounter.admission_year == admission_year,
        )
    ).first()
    if not counter:
        counter = RollCounter(
            department_id=dept.id,
            admission_year=admission_year,
            last_serial=100,
        )
        session.add(counter)
        session.flush()

    counter.last_serial += 1
    session.add(counter)
    session.flush()

    year_part = str(admission_year)[-2:]
    branch_part = dept.code.upper()
    serial_part = f"{counter.last_serial:03d}"
    roll_number = f"{year_part}{branch_part}{serial_part}"

    # 2. Ensure Batch exists for this department + admission_year
    batch = session.exec(
        select(Batch).where(
            Batch.department_id == dept.id,
            Batch.start_year == admission_year,
        )
    ).first()
    if not batch:
        batch = Batch(
            department_id=dept.id,
            start_year=admission_year,
            end_year=admission_year + 4,
        )
        session.add(batch)
        session.flush()

    # 3. Find or create Section (A, then B, capacity 60)
    sections = session.exec(
        select(Section)
        .where(Section.batch_id == batch.id)
        .order_by(Section.name)
    ).all()

    chosen_section: Section | None = None
    for sec in sections:
        count_in_sec = session.exec(
            select(func.count(Student.id)).where(Student.section_id == sec.id)
        ).one()
        if count_in_sec < sec.capacity:
            chosen_section = sec
            break

    if not chosen_section:
        next_letter = chr(ord("A") + len(sections))
        chosen_section = Section(
            batch_id=batch.id,
            name=next_letter,
            current_year=1,
            current_semester=1,
            capacity=60,
        )
        session.add(chosen_section)
        session.flush()

    # 4. Find or create MentorGroup (capacity 30) inside chosen_section
    groups = session.exec(
        select(MentorGroup)
        .where(MentorGroup.section_id == chosen_section.id)
        .order_by(MentorGroup.id)
    ).all()

    chosen_group: MentorGroup | None = None
    for grp in groups:
        count_in_grp = session.exec(
            select(func.count(Student.id)).where(Student.mentor_group_id == grp.id)
        ).one()
        if count_in_grp < grp.capacity:
            chosen_group = grp
            break

    if not chosen_group:
        # Pick an available mentor in this department, or fallback to HOD if none seeded yet
        dept_mentors = session.exec(
            select(User).where(
                User.department_id == dept.id,
                User.role == Role.mentor,
                User.is_active == True,  # noqa: E712
            )
        ).all()
        used_mentor_ids = {
            m_id
            for m_id in session.exec(select(MentorGroup.mentor_user_id)).all()
        }
        available_mentor = next(
            (m for m in dept_mentors if m.id not in used_mentor_ids),
            dept_mentors[0] if dept_mentors else hod_user,
        )
        group_num = len(groups) + 1
        chosen_group = MentorGroup(
            section_id=chosen_section.id,
            name=f"{dept.code}-{chosen_section.name} Group {group_num}",
            mentor_user_id=available_mentor.id,
            capacity=30,
        )
        session.add(chosen_group)
        session.flush()

    mentor_user = session.get(User, chosen_group.mentor_user_id) or hod_user

    # 5. Create Student User account
    temp_password = _generate_temp_password()
    student_user = User(
        username=roll_number,
        full_name=reg.full_name,
        email=reg.email,
        password_hash=hash_password(temp_password),
        role=Role.student,
        department_id=dept.id,
        is_active=True,
        must_change_password=True,
    )
    session.add(student_user)
    session.flush()

    # 6. Create Student profile
    student = Student(
        user_id=student_user.id,
        roll_number=roll_number,
        full_name=reg.full_name,
        dob=reg.dob,
        gender=reg.gender,
        phone=reg.phone,
        email=reg.email,
        parent_name=reg.parent_name,
        department_id=dept.id,
        batch_id=batch.id,
        section_id=chosen_section.id,
        mentor_group_id=chosen_group.id,
        quota=reg.quota,
        admission_year=admission_year,
        status="active",
    )
    session.add(student)
    session.flush()

    # 7. Update Registration status
    reg.status = RegistrationStatus.approved
    reg.decided_at = datetime.now(timezone.utc)
    reg.decided_by_user_id = hod_user.id
    reg.student_id = student.id
    if remarks and remarks.strip():
        reg.hod_remarks = remarks.strip()
    session.add(reg)

    return ApprovalOutcome(
        student=student,
        department=dept,
        section=chosen_section,
        mentor_group=chosen_group,
        mentor_user=mentor_user,
        username=roll_number,
        temp_password=temp_password,
        year_part=year_part,
        branch_part=branch_part,
        serial_part=serial_part,
    )