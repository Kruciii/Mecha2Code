import argparse
import json
import sys
from pathlib import Path

from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
import models

DEFAULT_MODULE_NAMES = {
    1: "Zadania do Samokontroli",
    2: "Zaawansowane mechanizmy i idiomy Pythona",
}


def load_json_data(file_path: str | None) -> dict:
    # 1. If explicit file path is provided and exists:
    if file_path:
        p = Path(file_path)
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        raise FileNotFoundError(f"Nie znaleziono wskazanego pliku: {file_path}")

    # 2. Check standard search locations
    search_paths = [
        Path("Misc/tasks_batch.json"),
        Path("../Misc/tasks_batch.json"),
        Path(__file__).resolve().parent.parent / "Misc" / "tasks_batch.json",
        Path("tasks_batch.json"),
    ]
    for p in search_paths:
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)

    # 3. Fallback to stdin (e.g. when piped via docker exec -i)
    if not sys.stdin.isatty():
        return json.load(sys.stdin)

    raise FileNotFoundError(
        "Nie znaleziono tasks_batch.json w standardowych lokalizacjach (Misc/tasks_batch.json) "
        "ani na wejściu standardowym (stdin)."
    )


def ensure_course(db: Session, course_id: int) -> models.Course:
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if course is None:
        print(f"Kurs o id={course_id} nie istnieje. Tworzę nowy kurs...")
        course = models.Course(
            id=course_id,
            title="Programowanie w Pythonie",
            description="Kurs programowania w języku Python: od podstaw do zaawansowanych mechanizmów.",
        )
        db.add(course)
        db.flush()
    print(f"Wybrany kurs: [ID={course.id}] '{course.title}'")
    return course


def resolve_course_modules(db: Session, course: models.Course, batch_module_ids: set[int]) -> dict[int, models.Module]:
    """Map each batch module_id (e.g. 1, 2) to a DB Module belonging to this specific course."""
    existing_modules = (
        db.query(models.Module)
        .filter(models.Module.course_id == course.id)
        .order_by(models.Module.order_index, models.Module.id)
        .all()
    )

    module_map: dict[int, models.Module] = {}

    for batch_mod_id in sorted(batch_module_ids):
        # 1. Look for existing module with same order_index
        matched = next((m for m in existing_modules if m.order_index == batch_mod_id), None)

        # 2. Look for existing module with expected title
        expected_title = DEFAULT_MODULE_NAMES.get(batch_mod_id, f"Moduł {batch_mod_id}")
        if not matched:
            matched = next((m for m in existing_modules if m.title.lower() == expected_title.lower()), None)

        # 3. Create if not found
        if not matched:
            print(f"Tworzę nowy moduł dla kursu {course.id}: '{expected_title}' (order_index={batch_mod_id})")
            matched = models.Module(
                course_id=course.id,
                title=expected_title,
                order_index=batch_mod_id,
            )
            db.add(matched)
            db.flush()
            existing_modules.append(matched)

        module_map[batch_mod_id] = matched
        print(f"  Mapowanie: Moduł w batchu #{batch_mod_id} -> DB Moduł [ID={matched.id}] '{matched.title}'")

    return module_map


def import_batch(course_id: int, file_path: str | None = None, dry_run: bool = False, clear_existing: bool = False):
    data = load_json_data(file_path)
    items = data.get("items", [])
    if not items:
        print("Plik nie zawiera żadnych zadań w 'items'.")
        return

    print(f"\nRozpoczynanie importu {len(items)} zadań do kursu o ID={course_id}...")
    if dry_run:
        print("TRYB DRY-RUN: Żadne zmiany nie zostaną zapisane w bazie.")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        course = ensure_course(db, course_id)
        batch_mod_ids = {int(item["module_id"]) for item in items}
        module_map = resolve_course_modules(db, course, batch_mod_ids)

        if clear_existing:
            target_module_ids = [m.id for m in module_map.values()]
            print(f"Czyszczenie istniejących zadań w modułach: {target_module_ids}...")
            if not dry_run:
                db.query(models.Task).filter(models.Task.module_id.in_(target_module_ids)).delete(synchronize_session=False)
                db.flush()

        created_tasks = 0
        updated_tasks = 0
        total_test_cases = 0

        for index, item in enumerate(items, start=1):
            batch_mod_id = int(item["module_id"])
            target_module = module_map[batch_mod_id]
            task_info = item["task"]
            test_cases_info = item.get("test_cases", [])

            title = task_info["title"].strip()
            description = task_info["description"]
            time_limit = float(task_info.get("time_limit", 2.0))
            memory_limit = int(task_info.get("memory_limit", 128000))
            tags = str(task_info.get("tags", "łatwe")).strip() or "łatwe" 

            existing_task = (
                db.query(models.Task)
                .filter(
                    models.Task.module_id == target_module.id,
                    models.Task.title == title,
                )
                .first()
            )

            if existing_task:
                if not dry_run:
                    existing_task.description = description
                    existing_task.time_limit = time_limit
                    existing_task.memory_limit = memory_limit
                    existing_task.tags = tags
                    # Usuń stare test case'y i wstaw nowe
                    db.query(models.TestCase).filter(models.TestCase.task_id == existing_task.id).delete()
                    for tc in test_cases_info:
                        db.add(
                            models.TestCase(
                                task_id=existing_task.id,
                                input_data=tc["input_data"],
                                expected_output=tc["expected_output"],
                                is_hidden=bool(tc.get("is_hidden", False)),
                            )
                        )
                updated_tasks += 1
                task_id_label = f"ID={existing_task.id}"
            else:
                if not dry_run:
                    new_task = models.Task(
                        module_id=target_module.id,
                        title=title,
                        description=description,
                        time_limit=time_limit,
                        memory_limit=memory_limit,
                        tags=tags,
                    )
                    db.add(new_task)
                    db.flush()
                    for tc in test_cases_info:
                        db.add(
                            models.TestCase(
                                task_id=new_task.id,
                                input_data=tc["input_data"],
                                expected_output=tc["expected_output"],
                                is_hidden=bool(tc.get("is_hidden", False)),
                            )
                        )
                    task_id_label = f"nowe ID={new_task.id}"
                else:
                    task_id_label = "nowe (dry-run)"
                created_tasks += 1

            total_test_cases += len(test_cases_info)
            print(f"  [{index:02d}/{len(items):02d}] {title} -> Moduł {target_module.id} ({task_id_label}, {len(test_cases_info)} testów)")

        if dry_run:
            db.rollback()
            print(f"\n[DRY RUN] Zwalidowano pomyślnie: {created_tasks} nowych, {updated_tasks} do aktualizacji, łącznie {total_test_cases} test cases.")
        else:
            db.commit()
            print(f"\nSUKCES! Zapisano w bazie: {created_tasks} nowych zadań, {updated_tasks} zaktualizowanych, {total_test_cases} test cases.")
            print(f"Wszystkie zadania są przypisane do kursu ID={course.id} ('{course.title}').")

    except Exception as exc:
        db.rollback()
        print(f"\nBłąd podczas importu: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Import tasks_batch.json into a course in MechaCode database.")
    parser.add_argument("--course-id", type=int, default=3, help="ID kursu docelowego (domyślnie: 3)")
    parser.add_argument("--file", type=str, default=None, help="Ścieżka do tasks_batch.json")
    parser.add_argument("--dry-run", action="store_true", help="Tylko walidacja, bez zapisu do bazy")
    parser.add_argument("--clear-existing", action="store_true", help="Usuń wcześniejsze zadania w tych modułach przed importem")
    args = parser.parse_args()

    import_batch(
        course_id=args.course_id,
        file_path=args.file,
        dry_run=args.dry_run,
        clear_existing=args.clear_existing,
    )


if __name__ == "__main__":
    main()

