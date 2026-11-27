import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlmodel import Session, select
from app.database import create_db_and_tables, engine
from app.models.academics import Department
from app.models.users import Role, User
from app.security import hash_password

DEPARTMENTS = [
    ("CSE", "Computer Science and Engineering", 120),
    ("ECE", "Electronics and Communication Engineering", 120),
    ("EEE", "Electrical and Electronics Engineering", 120),
    ("MECH", "Mechanical Engineering", 120),
    ("CIVIL", "Civil Engineering", 120),
]

HODS = [
    ("CSE", "hod.cse@college.edu", "Dr. Ramesh Kumar (CSE HOD)"),
    ("ECE", "hod.ece@college.edu", "Dr. Priya Sharma (ECE HOD)"),
]


def main() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        for code, name, intake in DEPARTMENTS:
            dept = session.exec(select(Department).where(Department.code == code)).first()
            if not dept:
                session.add(Department(code=code, name=name, intake=intake))
        session.commit()

        for code, email, full_name in HODS:
            dept = session.exec(select(Department).where(Department.code == code)).first()
            user = session.exec(select(User).where(User.username == email)).first()
            if not user:
                user = User(
                    username=email,
                    full_name=full_name,
                    email=email,
                    password_hash=hash_password("Hod@123"),
                    role=Role.hod,
                    department_id=dept.id,
                    is_active=True,
                    must_change_password=False,
                )
                session.add(user)
                session.commit()
                session.refresh(user)
            dept.hod_user_id = user.id
            session.add(dept)
        session.commit()

    print("HOD test accounts ready:")
    print("  CSE HOD -> hod.cse@college.edu / Hod@123")
    print("  ECE HOD -> hod.ece@college.edu / Hod@123")


if __name__ == "__main__":
    main()