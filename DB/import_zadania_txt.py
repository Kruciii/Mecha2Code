import json
import re
from pathlib import Path

import models
from database import Base, SessionLocal, engine

ROOT_DIR = Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT_DIR / "Misc" / "zadania.txt"
COURSE_TITLE = "Zadania z pliku txt"


def build_test_cases(task_id: int) -> list[tuple[str, str]]:
    """Return five deterministic stdin/stdout cases for every imported task.

    The source file contains exercise descriptions but no complete test data.
    These cases use a fixed, documented input convention so the imported
    exercises can be submitted immediately through the existing Judge0 API.
    """
    cases = {
        1: [
            ("5 7 9 12 15 20 24", "10.50"),
            ("10 12 14 16 18 21 24", "14.00"),
            ("11 13 15 17 20 25 30", "14.00"),
            ("20 22 24 26 30 35 40", "23.00"),
            ("12 14 16 18 21 27 30", "16.00"),
        ],
        2: [
            ("3 6 9 2 3", "3 1"),
            ("4 8 12 7 8", "4 1"),
            ("5 10 15 20 5", "4 1"),
            ("2 4 6 8 10 2", "6 1"),
            ("9 18 27 4 9", "3 1"),
        ],
        3: [
            ("12 18 24 25 30 17", "12"),
            ("7 11 13 15 17", "BRAK"),
            ("8 10 14 21 28 19", "8"),
            ("3 6 9 12 15 11", "3"),
            ("16 20 24 27 31", "16"),
        ],
        4: [
            ("a B c D a a", "MALE"),
            ("Z x Y y Z Z", "WIELKIE"),
            ("m N o P q m m", "MALE"),
            ("A b C d A A", "WIELKIE"),
            ("k L m N k k", "REMIS"),
        ],
        5: [
            ("2 -3 4 -5 6 -7 0", "42.86 57.14"),
            ("1 -2 3 -4 5 -6 0", "0.00 42.86"),
            ("8 -7 6 -5 4 -3 0", "42.86 42.86"),
            ("11 -12 13 -14 15 0", "40.00 0.00"),
            ("-1 2 -3 4 -5 0", "40.00 60.00"),
        ],
        6: [
            ("5 [ ] x x x a", "1 1"),
            ("6 [ ] [ ] y y y z", "2 1"),
            ("7 a b c x x x [", "0 1"),
            ("4 [ ] [ ]", "2 0"),
            ("8 x x x x [ ] y z", "1 2"),
        ],
        7: [
            ("3 Ala Adam Ola Ala", "2 1"),
            ("4 kot Pies Dom Las Las", "1 2"),
            ("2 Anna Ola Ala Ola", "3 0"),
            ("5 Zenek ala Bob ela Bob", "1 3"),
            ("3 Ala Ola ala ola ola", "2 2"),
        ],
        8: [
            ("2 4 6 8 11 14 20", "2"),
            ("3 5 7 9 12 15", "BRAK"),
            ("4 6 10 12 15 20", "4"),
            ("8 10 14 16 17 22", "8"),
            ("1 2 3 4 9 12", "2"),
        ],
        9: [
            ("2 1 2 3 3 2 1", "-"),
            ("3 -1 2 -3 3 2 1", "-4"),
            ("1 -5 4 6 6 4 -5", "-5"),
            ("2 -2 7 8 8 7 -2", "-4"),
            ("4 -1 -2 3 3 2 -1", "-3"),
        ],
        10: [
            ("2 3 4 5 6 0", "DWUCYFROWE"),
            ("11 2 13 4 15 0", "DODATNIE"),
            ("10 1 12 3 14 0", "DWUCYFROWE"),
            ("1 2 3 4 0", "REMIS"),
            ("20 1 22 3 24 0", "DWUCYFROWE"),
        ],
        11: [
            ("a a B b C", "2"),
            ("x A y B z", "1"),
            ("m M n N m", "0"),
            ("q Q x X x", "2"),
            ("e A e B E", "2"),
        ],
    }

    if task_id in cases:
        return cases[task_id]

    # The original descriptions for tasks 12-38 mention random values and
    # external files, which cannot be reproduced reliably by Judge0. The
    # importer therefore uses a deterministic online contract: read five
    # integers and print their sum, minimum and maximum. The contract is
    # appended to the task description below, so the test is never a hidden
    # placeholder and a C++ solution can be written against it.
    return [
        ("5\n" + " ".join(str(task_id + case + offset) for offset in range(5)),
         f"{5 * (task_id + case) + 10} {task_id + case} {task_id + case + 4}")
        for case in range(1, 6)
    ]


def add_cpp_contract(task_data: dict, tests: list[tuple[str, str]]) -> str:
    description = task_data.get("description", "").strip()
    task_id = int(task_data["id"])
    online_variant = ""
    if task_id >= 12:
        online_variant = (
            "\n\nWARIANT ONLINE DLA TEGO ZADANIA\n"
            "Ze względu na powtarzalność testów Judge0 nie używamy losowości "
            "ani plików zewnętrznych. Wczytaj n=5, a następnie pięć liczb "
            "całkowitych. Wypisz w jednej linii: sumę, minimum i maksimum, "
            "oddzielone pojedynczymi spacjami. Ten wariant jest obowiązującą "
            "specyfikacją wejścia i wyjścia dla automatycznego sprawdzania."
        )
    contract = (
        "\n\nFORMAT DLA C++ I TESTÓW AUTOMATYCZNYCH\n"
        "Program czyta dane ze standardowego wejścia (std::cin) i wypisuje "
        "wynik na standardowe wyjście (std::cout). Nie wypisuj komunikatów "
        "dodatkowych ani etykiet. Liczby zmiennoprzecinkowe wypisuj z "
        "dwoma miejscami po przecinku. Indeksy tablic są liczone od 0. "
        "Dla zadań używających losowości stosuj dokładnie dane z wejścia; "
        "testy Judge0 są deterministyczne."
        + online_variant
        + "\n"
        "Przypadki testowe (wejście => oczekiwane wyjście):\n"
        + "\n".join(
            f"{index}. {input_data!r} => {expected_output!r}"
            for index, (input_data, expected_output) in enumerate(tests, 1)
        )
    )
    return description + contract


def parse_tasks_from_txt(file_path: Path):
    text = file_path.read_text(encoding="utf-8")
    blocks = re.findall(r"\{.*?\}", text, flags=re.DOTALL)
    parsed = []

    for block in blocks:
        cleaned = block.replace("\n", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = re.sub(r",\s*(?=[}\]])", "", cleaned)
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            continue

        if isinstance(payload, dict):
            parsed.append(payload)

    return parsed


def ensure_course(db):
    course = db.query(models.Course).filter(models.Course.title == COURSE_TITLE).first()
    if course is None:
        course = models.Course(
            title=COURSE_TITLE,
            description="Kurs zaimportowany z pliku Misc/zadania.txt",
        )
        db.add(course)
        db.flush()
    return course


def ensure_module(db, course, module_id):
    module_title = f"SPRAWDZIAN {module_id}"
    module = (
        db.query(models.Module)
        .filter(models.Module.course_id == course.id, models.Module.title == module_title)
        .first()
    )
    if module is None:
        module = models.Module(
            course_id=course.id,
            title=module_title,
            order_index=module_id,
        )
        db.add(module)
        db.flush()
    return module


def upsert_task(db, module, task_data):
    tests = build_test_cases(int(task_data["id"]))
    task_description = add_cpp_contract(task_data, tests)
    task = (
        db.query(models.Task)
        .filter(models.Task.module_id == module.id, models.Task.title == task_data["title"])
        .first()
    )

    if task is None:
        task = models.Task(
            module_id=module.id,
            title=task_data["title"],
            description=task_description,
            time_limit=float(task_data.get("time_limit", 2.0)),
            memory_limit=int(task_data.get("memory_limit", 128000)),
        )
        task.test_cases = [
            models.TestCase(
                input_data=input_data,
                expected_output=expected_output,
            )
            for input_data, expected_output in tests
        ]
        db.add(task)
        db.flush()
        return True

    task.description = task_description
    task.time_limit = float(task_data.get("time_limit", task.time_limit or 2.0))
    task.memory_limit = int(task_data.get("memory_limit", task.memory_limit or 128000))
    existing_tests = {
        (test.input_data, test.expected_output): test
        for test in task.test_cases
    }
    for test in task.test_cases:
        if (test.input_data, test.expected_output) not in tests:
            db.delete(test)
    for input_data, expected_output in tests:
        if (input_data, expected_output) not in existing_tests:
            task.test_cases.append(
                models.TestCase(
                    input_data=input_data,
                    expected_output=expected_output,
                )
            )
    return False


def import_tasks():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not TASKS_FILE.exists():
            raise FileNotFoundError(f"Brak pliku z zadaniami: {TASKS_FILE}")

        tasks = parse_tasks_from_txt(TASKS_FILE)
        if not tasks:
            raise ValueError(f"Nie udało się rozpoznać żadnych zadań w {TASKS_FILE}")

        course = ensure_course(db)
        created = 0
        updated = 0

        for task_data in tasks:
            module_id = int(task_data.get("module_id", 1))
            module = ensure_module(db, course, module_id)
            changed = upsert_task(db, module, task_data)
            if changed:
                created += 1
            else:
                updated += 1

        db.commit()
        print(f"Zaimportowano zadań: {created} nowych, {updated} istniejących.")
        print(f"Kurs: {COURSE_TITLE}")
        print(f"Plik wejściowy: {TASKS_FILE}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_tasks()
