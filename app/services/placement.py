from typing import Optional
from sqlmodel import Session, func, select

from app.models.academics import Batch, Department, MentorGroup, Section, Student


def get_or_create_batch(
    session: Session,
    department: Department,
    admission_year: int,
) -> Batch:
    """Find the existing batch for (department, admission_year) or create a 4-year B.Tech batch."""
    batch = session.exec(
        select(Batch).where(
            Batch.department_id == department.id,
            Batch.start_year == admission_year,
        )
    ).first()

    if not batch:
        batch = Batch(
            department_id=department.id,
            start_year=admission_year,
            end_year=admission_year + 4,
        )
        session.add(batch)
        session.flush()

    return batch


def pick_section(session: Session, batch: Batch) -> Section:
    """
    Return the section in `batch` with the fewest students that is still below its capacity.
    If no sections exist yet or all existing sections are full, create the next section (A, B, C...)
    with current_year=1, current_semester=1.
    """
    sections = session.exec(
        select(Section)
        .where(Section.batch_id == batch.id)
        .order_by(Section.name)
    ).all()

    best_section: Optional[Section] = None
    lowest_count: Optional[int] = None

    for sec in sections:
        student_count = session.exec(
            select(func.count(Student.id)).where(Student.section_id == sec.id)
        ).one()
        if student_count < sec.capacity:
            if lowest_count is None or student_count < lowest_count:
                lowest_count = student_count
                best_section = sec

    if best_section is not None:
        return best_section

    next_letter = chr(ord("A") + len(sections))
    new_section = Section(
        batch_id=batch.id,
        name=next_letter,
        current_year=1,
        current_semester=1,
        capacity=60,
    )
    session.add(new_section)
    session.flush()
    return new_section


def pick_mentor_group(session: Session, section: Section) -> Optional[MentorGroup]:
    """
    Return the mentor group in `section` with fewer than 30 students (and below its capacity)
    that currently has the fewest students. Returns None if no mentor group has space.
    """
    groups = session.exec(
        select(MentorGroup)
        .where(MentorGroup.section_id == section.id)
        .order_by(MentorGroup.id)
    ).all()

    best_group: Optional[MentorGroup] = None
    lowest_count: Optional[int] = None

    for grp in groups:
        max_allowed = min(30, grp.capacity)
        student_count = session.exec(
            select(func.count(Student.id)).where(Student.mentor_group_id == grp.id)
        ).one()
        if student_count < max_allowed:
            if lowest_count is None or student_count < lowest_count:
                lowest_count = student_count
                best_group = grp

    return best_group