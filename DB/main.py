from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine
import models
import schemas

# Jeśli tabele jeszcze nie istnieją, ta linijka je stworzy (przydatne przed ustawieniem Alembica)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MechaCode API")

# ----------------- USERS -----------------
@app.get("/users/", response_model=list[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Sprawdzenie czy email już istnieje
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Ten email jest już zajęty.")

    new_user = models.User(
        email=user.email,
        role=user.role,
        # TODO: Zmienić na prawdziwe haszowanie (np. passlib / bcrypt)
        hashed_password=f"fake_hashed_{user.password}" 
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ----------------- COURSES -----------------
@app.get("/courses/", response_model=list[schemas.CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    return db.query(models.Course).all()

@app.post("/courses/", response_model=schemas.CourseResponse)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    new_course = models.Course(
        title=course.title,
        description=course.description
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


# ----------------- TASKS -----------------
@app.post("/tasks/", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    module = db.query(models.Module).filter(models.Module.id == task.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Nie znaleziono modułu dla tego zadania.")

    new_task = models.Task(
        module_id=task.module_id,
        title=task.title,
        description=task.description,
        time_limit=task.time_limit,
        memory_limit=task.memory_limit,
    )
    db.add(new_task)
    db.flush()

    for test_case in task.test_cases:
        db.add(
            models.TestCase(
                task_id=new_task.id,
                input_data=test_case.input_data,
                expected_output=test_case.expected_output,
                is_hidden=test_case.is_hidden,
            )
        )

    db.commit()
    db.refresh(new_task)
    return new_task


@app.post("/courses/{course_id}/tasks-batch", response_model=schemas.TaskBatchCreateResponse)
def create_tasks_batch(course_id: int, payload: schemas.TaskBatchCreateRequest, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Nie znaleziono kursu.")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Batch jest pusty.")

    module_ids = {item.module_id for item in payload.items}
    modules = db.query(models.Module).filter(models.Module.id.in_(module_ids)).all()
    module_to_course = {module.id: module.course_id for module in modules}

    missing_modules = [module_id for module_id in module_ids if module_id not in module_to_course]
    if missing_modules:
        raise HTTPException(
            status_code=400,
            detail=f"Nie znaleziono modułów o id: {missing_modules}",
        )

    wrong_course_modules = [
        module_id
        for module_id, module_course_id in module_to_course.items()
        if module_course_id != course_id
    ]
    if wrong_course_modules:
        raise HTTPException(
            status_code=400,
            detail=(
                "Następujące moduły nie należą do tego kursu: "
                f"{wrong_course_modules}"
            ),
        )

    for index, item in enumerate(payload.items, start=1):
        if not item.task.title.strip():
            raise HTTPException(status_code=400, detail=f"Pozycja {index}: title nie może być puste.")
        if item.task.time_limit <= 0:
            raise HTTPException(status_code=400, detail=f"Pozycja {index}: time_limit musi być > 0.")
        if item.task.memory_limit <= 0:
            raise HTTPException(status_code=400, detail=f"Pozycja {index}: memory_limit musi być > 0.")
        if not item.test_cases:
            raise HTTPException(status_code=400, detail=f"Pozycja {index}: wymagany co najmniej 1 test case.")
        for test_index, test_case in enumerate(item.test_cases, start=1):
            if not test_case.input_data.strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"Pozycja {index}, test {test_index}: input_data nie może być puste.",
                )
            if not test_case.expected_output.strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"Pozycja {index}, test {test_index}: expected_output nie może być puste.",
                )

    if payload.dry_run:
        total_tests = sum(len(item.test_cases) for item in payload.items)
        return schemas.TaskBatchCreateResponse(
            course_id=course_id,
            created_tasks=len(payload.items),
            created_test_cases=total_tests,
            task_ids=[],
            dry_run=True,
            message="Dry run OK. Walidacja zakończona powodzeniem, nic nie zapisano.",
        )

    created_task_ids: list[int] = []
    created_test_cases = 0

    try:
        for item in payload.items:
            new_task = models.Task(
                module_id=item.module_id,
                title=item.task.title,
                description=item.task.description,
                time_limit=item.task.time_limit,
                memory_limit=item.task.memory_limit,
            )
            db.add(new_task)
            db.flush()
            created_task_ids.append(new_task.id)

            for test_case in item.test_cases:
                db.add(
                    models.TestCase(
                        task_id=new_task.id,
                        input_data=test_case.input_data,
                        expected_output=test_case.expected_output,
                        is_hidden=test_case.is_hidden,
                    )
                )
                created_test_cases += 1

        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Błąd podczas zapisu batcha zadań.")

    return schemas.TaskBatchCreateResponse(
        course_id=course_id,
        created_tasks=len(created_task_ids),
        created_test_cases=created_test_cases,
        task_ids=created_task_ids,
        dry_run=False,
        message="Batch zadań został zapisany.",
    )


# ----------------- SUBMISSIONS -----------------
@app.post("/submissions/", response_model=schemas.TaskSubmissionResponse)
def create_submission(sub: schemas.TaskSubmissionCreate, db: Session = Depends(get_db)):
    # Tutaj w przyszłości będzie strzał do API Judge0 na serwerze!
    # Na razie po prostu zapisujemy zgłoszenie w bazie (status = In Queue / Przetwarzanie)
    
    new_submission = models.TaskSubmission(
        user_id=sub.user_id,
        task_id=sub.task_id,
        source_code=sub.source_code,
        language_id=sub.language_id,
        status_id=1, # 1 = In Queue (oczekuje na Judge0)
        attempt_number=1 # TODO: logika sprawdzająca numer próby w historii
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)
    
    return new_submission