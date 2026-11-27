import sys
from pathlib import Path

# Ensure project root is on sys.path when running `python scripts/create_admin.py`
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlmodel import Session, select
from app.database import create_db_and_tables, engine
from app.models.users import Role, User
from app.security import hash_password


def main() -> None:
    create_db_and_tables()
    email = "management@college.edu"

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == email)).first()
        if existing:
            print(f"Admin user already exists: {email}")
            return

        admin_user = User(
            username=email,
            full_name="College Management",
            email=email,
            password_hash=hash_password("Admin@123"),
            role=Role.management,
            is_active=True,
            must_change_password=False,
        )
        session.add(admin_user)
        session.commit()
        print("Created management user: management@college.edu / Admin@123")


if __name__ == "__main__":
    main()