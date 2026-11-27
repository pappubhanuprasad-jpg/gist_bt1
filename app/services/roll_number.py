from sqlmodel import Session, select
from app.models.academics import Department, RollCounter


def next_roll_number(session: Session, department: Department, admission_year: int) -> str:
    """
    Generate the next sequential roll number for a department and admission year
    in the format YY + BRANCH + 3-digit serial (e.g. 26CSE001, 26CSE115).
    """
    # Why a dedicated RollCounter table is safer than counting rows in Student:
    # 1. If a student drops out, is deleted, or transfers out, COUNT(students) shrinks and
    #    would issue a duplicate roll number to the next admitted student.
    # 2. The counter row acts as an atomic sequence point per (department_id, admission_year),
    #    preventing two simultaneous approvals from ever calculating the same serial.
    counter = session.exec(
        select(RollCounter).where(
            RollCounter.department_id == department.id,
            RollCounter.admission_year == admission_year,
        )
    ).first()

    if not counter:
        counter = RollCounter(
            department_id=department.id,
            admission_year=admission_year,
            last_serial=0,
        )
        session.add(counter)
        session.flush()

    counter.last_serial += 1
    serial = counter.last_serial
    session.add(counter)
    session.flush()

    return f"{admission_year % 100:02d}{department.code.upper()}{serial:03d}"