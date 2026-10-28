import sys
from passlib.context import CryptContext
from sqlalchemy import func
from database import SessionLocal
import models

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_EMAIL = "admin@mechacode.local"
ADMIN_PASSWORD = "admin"


def reset_admin():
    db = SessionLocal()
    try:
        # 1. Usunięcie starych kont z fake_hashed_
        fake_users = (
            db.query(models.User)
            .filter(models.User.hashed_password.like("fake_hashed_%"))
            .all()
        )
        for u in fake_users:
            print(f"Usuwanie konta ze starym hashem: {u.email} (id={u.id})")
            db.delete(u)

        # 2. Utworzenie lub nadpisanie hasła admina prawdziwym bcryptem
        admin = (
            db.query(models.User)
            .filter(func.lower(models.User.email) == ADMIN_EMAIL.lower())
            .first()
        )
        real_hash = password_context.hash(ADMIN_PASSWORD)

        if admin is None:
            print(f"Tworzenie nowego administratora: {ADMIN_EMAIL}")
            admin = models.User(
                email=ADMIN_EMAIL,
                role="admin",
                hashed_password=real_hash,
                semester=1,
                start_year=2026,
                major="mechatro",
            )
            db.add(admin)
        else:
            print(f"Nadpisywanie hasła istniejącego admina ({ADMIN_EMAIL}) hashem bcrypt...")
            admin.role = "admin"
            admin.hashed_password = real_hash
            admin.semester = 1
            admin.start_year = 2026
            admin.major = "mechatro"
            db.add(admin)

        db.commit()
        print("\nSukces! Konto administratora jest gotowe:")
        print(f"  Email: {ADMIN_EMAIL}")
        print(f"  Hasło: {ADMIN_PASSWORD}")
    except Exception as exc:
        db.rollback()
        print(f"Błąd: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_admin()
