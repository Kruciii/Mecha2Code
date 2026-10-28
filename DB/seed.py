from passlib.context import CryptContext

import models
from database import Base, SessionLocal, engine


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USER_EMAIL = "user@mechacode.local"
USER_PASSWORD = "user"
COURSE_TITLE = "Programowanie 1"
MODULE_TITLE = "Podstawy C++"
TASK_TITLE = "Suma dwóch liczb"


def seed_database() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        user = db.query(models.User).filter(models.User.email == USER_EMAIL).first()
        if user is None:
            user = models.User(
                email=USER_EMAIL,
                role="student",
                hashed_password=password_context.hash(USER_PASSWORD),
            )
            db.add(user)

        course = (
            db.query(models.Course)
            .filter(models.Course.title == COURSE_TITLE)
            .first()
        )
        if course is None:
            course = models.Course(
                title=COURSE_TITLE,
                description="Wprowadzenie do programowania w języku C++.",
            )
            db.add(course)
            db.flush()

        module = (
            db.query(models.Module)
            .filter(
                models.Module.course_id == course.id,
                models.Module.title == MODULE_TITLE,
            )
            .first()
        )
        if module is None:
            module = models.Module(
                course_id=course.id,
                title=MODULE_TITLE,
                order_index=1,
            )
            db.add(module)
            db.flush()

        task = (
            db.query(models.Task)
            .filter(
                models.Task.module_id == module.id,
                models.Task.title == TASK_TITLE,
            )
            .first()
        )
        if task is None:
            task = models.Task(
                module_id=module.id,
                title=TASK_TITLE,
                description=(
                    "Napisz program, który wczyta dwie liczby całkowite "
                    "i wypisze ich sumę."
                ),
                time_limit=2.0,
                memory_limit=128000,
            )
            task.test_cases = [
                models.TestCase(input_data="2 3", expected_output="5"),
                models.TestCase(input_data="-4 9", expected_output="5"),
            ]
            db.add(task)

        db.commit()
        print(f"Użytkownik: {USER_EMAIL} / {USER_PASSWORD}")
        print(f"Zadanie: {TASK_TITLE}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
