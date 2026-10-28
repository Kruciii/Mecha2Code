from passlib.context import CryptContext

import models
from database import Base, SessionLocal, engine


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_EMAIL = "admin@mechacode.local"
ADMIN_PASSWORD = "admin"
COURSE_TITLE = "Zadania przykładowe"
MODULE_TITLE = "Podstawy programowania"

TASKS = [
    {
        "title": "Suma dwóch liczb",
        "description": (
            "Wczytaj dwie liczby całkowite i wypisz ich sumę."
        ),
        "tests": [
            ("2 3", "5"),
            ("-4 9", "5"),
        ],
    },
    {
        "title": "Największa z trzech liczb",
        "description": (
            "Wczytaj trzy liczby całkowite i wypisz największą z nich."
        ),
        "tests": [
            ("4 9 2", "9"),
            ("-5 -2 -8", "-2"),
        ],
    },
    {
        "title": "Parzysta czy nieparzysta",
        "description": (
            "Wczytaj liczbę całkowitą. Wypisz PARZYSTA, jeśli jest parzysta, "
            "albo NIEPARZYSTA w przeciwnym przypadku."
        ),
        "tests": [
            ("8", "PARZYSTA"),
            ("13", "NIEPARZYSTA"),
        ],
    },
    {
        "title": "Silnia",
        "description": (
            "Wczytaj nieujemną liczbę całkowitą n i wypisz wartość n!."
        ),
        "tests": [
            ("0", "1"),
            ("5", "120"),
        ],
    },
    {
        "title": "Odwrócony napis",
        "description": (
            "Wczytaj jedno słowo i wypisz je od końca do początku."
        ),
        "tests": [
            ("mecha", "ahcem"),
            ("code", "edoc"),
        ],
    },
]


def get_or_create_admin(db):
    # Usunięcie starych kont ze sztucznymi haszami
    db.query(models.User).filter(models.User.hashed_password.like("fake_hashed_%")).delete(synchronize_session=False)

    admin = (
        db.query(models.User)
        .filter(models.User.email == ADMIN_EMAIL)
        .first()
    )
    new_hashed = password_context.hash(ADMIN_PASSWORD)
    if admin is None:
        admin = models.User(
            email=ADMIN_EMAIL,
            role="admin",
            hashed_password=new_hashed,
            semester=1,
            start_year=2026,
            major="mechatro",
        )
        db.add(admin)
    else:
        admin.role = "admin"
        admin.hashed_password = new_hashed
        admin.semester = 1
        admin.start_year = 2026
        admin.major = "mechatro"
        db.add(admin)
    return admin


def get_or_create_course(db):
    course = (
        db.query(models.Course)
        .filter(models.Course.title == COURSE_TITLE)
        .first()
    )
    if course is None:
        course = models.Course(
            title=COURSE_TITLE,
            description="Pięć zadań do sprawdzenia konfiguracji MechaCode.",
        )
        db.add(course)
        db.flush()
    return course


def get_or_create_module(db, course):
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
    return module


def add_tasks(db, module):
    created_count = 0
    for task_data in TASKS:
        task = (
            db.query(models.Task)
            .filter(
                models.Task.module_id == module.id,
                models.Task.title == task_data["title"],
            )
            .first()
        )
        if task is not None:
            continue

        task = models.Task(
            module_id=module.id,
            title=task_data["title"],
            description=task_data["description"],
            time_limit=2.0,
            memory_limit=128000,
        )
        task.test_cases = [
            models.TestCase(
                input_data=input_data,
                expected_output=expected_output,
            )
            for input_data, expected_output in task_data["tests"]
        ]
        db.add(task)
        created_count += 1
    return created_count


def seed_examples() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        get_or_create_admin(db)
        course = get_or_create_course(db)
        module = get_or_create_module(db, course)
        created_count = add_tasks(db, module)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"Utworzono nowych zadań: {created_count}/5")
    print(f"Login administratora: {ADMIN_EMAIL}")
    print(f"Hasło administratora: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    seed_examples()
