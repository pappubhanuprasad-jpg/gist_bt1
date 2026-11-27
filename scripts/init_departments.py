import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlmodel import Session, select
from app.database import create_db_and_tables, engine
from app.models.academics import Department

DEPARTMENTS = [
    ("CSE", "Computer Science and Engineering", 120),
    ("ECE", "Electronics and Communication Engineering", 120),
    ("EEE", "Electrical and Electronics Engineering", 120),
    ("MECH", "Mechanical Engineering", 120),
    ("CIVIL", "Civil Engineering", 120),
]


def main() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        for code, name, intake in DEPARTMENTS:
            existing = session.exec(select(Department).where(Department.code == code)).first()
            if not existing:
                session.add(Department(code=code, name=name, intake=intake))
        session.commit()
    print("Initialized 5 B.Tech departments (CSE, ECE, EEE, MECH, CIVIL).")


if __name__ == "__main__":
    main()