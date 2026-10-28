import os
import logging
import time
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import BackgroundTasks, FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal, get_db, engine
import models
import schemas
from judge0_client import Judge0Error, enqueue_batch, get_batch_results

BATCH_MAX_ITEMS = 100

# Jeśli tabele jeszcze nie istnieją, ta linijka je stworzy (przydatne przed ustawieniem Alembica)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MechaCode API")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Brak zmiennej JWT_SECRET_KEY w pliku .env!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def create_access_token(user: models.User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "email": user.email, "role": user.role, "exp": expires_at}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nieprawidłowy lub wygasły token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", ""))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def refresh_submission_from_judge0(
    submission: models.TaskSubmission,
) -> bool:
    """Fetch one Judge0 snapshot and aggregate it when every test is done."""
    pending_results = [
        result for result in submission.test_results
        if result.status_id in (None, 1, 2)
    ]
    if not pending_results:
        return True

    judge_results = get_batch_results(
        [result.judge0_token for result in pending_results]
    )
    results_by_token = {
        result.get("token"): result
        for result in judge_results
        if result.get("token")
    }
    for result in pending_results:
        judge_result = results_by_token.get(result.judge0_token)
        if judge_result is None:
            continue
        status_data = judge_result.get("status") or {}
        result.status_id = status_data.get("id")
        result.stdout = judge_result.get("stdout")
        result.stderr = judge_result.get("stderr")
        result.compile_output = judge_result.get("compile_output")
        result.execution_time = judge_result.get("time")
        result.memory_used = judge_result.get("memory")
        result.passed = result.status_id == 3

    finished = all(
        result.status_id not in (None, 1, 2)
        for result in submission.test_results
    )
    if finished:
        submission.passed_tests = sum(
            result.passed for result in submission.test_results
        )
        submission.total_tests = len(submission.test_results)
        submission.score = round(
            submission.passed_tests / submission.total_tests * 100,
            2,
        )
        submission.status_id = (
            3
            if submission.passed_tests == submission.total_tests
            else next(
                result.status_id
                for result in submission.test_results
                if not result.passed
            )
        )
        submission.error_count = sum(
            1
            for result in submission.test_results
            if result.stderr or result.compile_output
        )
    return finished


def process_submission(submission_id: int) -> None:
    """Poll Judge0 in the API background task and persist the final result."""
    db = SessionLocal()
    try:
        submission = db.query(models.TaskSubmission).filter(
            models.TaskSubmission.id == submission_id
        ).first()
        if submission is None:
            logger.error("Nie znaleziono zgłoszenia %s dla workera.", submission_id)
            return

        max_attempts = int(os.getenv("JUDGE0_MAX_POLL_ATTEMPTS", "40"))
        poll_interval = float(os.getenv("JUDGE0_POLL_INTERVAL_SECONDS", "1.5"))
        for _ in range(max_attempts):
            if refresh_submission_from_judge0(submission):
                db.commit()
                return
            db.commit()
            time.sleep(poll_interval)

        logger.error(
            "Przekroczono czas oczekiwania na Judge0 dla zgłoszenia %s.",
            submission_id,
        )
    except (Judge0Error, ValueError) as exc:
        db.rollback()
        logger.exception(
            "Nie udało się pobrać wyniku Judge0 dla zgłoszenia %s: %s",
            submission_id,
            exc,
        )
    finally:
        db.close()



def require_teacher_or_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if current_user.role.lower() not in {"admin", "teacher"}:
        raise HTTPException(
            status_code=403,
            detail="Brak uprawnień. Wymagana rola admin lub teacher.",
        )
    return current_user


def require_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="Brak uprawnień. Wymagana rola admin.",
        )
    return current_user

# ----------------- USERS -----------------
@app.get("/users/", response_model=list[schemas.UserResponse])
def get_users(
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(require_admin),
):
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
        # Rejestracja publiczna tworzy tylko konta studentów.
        role="student",
        hashed_password=password_context.hash(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ----------------- AUTH -----------------
@app.post("/login", response_model=schemas.TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if user is None or not password_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy email lub hasło.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(user), "token_type": "bearer"}


# ----------------- COURSES -----------------
@app.get("/courses/", response_model=list[schemas.CourseResponse])
def get_courses(
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Course).order_by(models.Course.id).all()


@app.get(
    "/courses/catalog/",
    response_model=list[schemas.CourseCatalogResponse],
)
def get_course_catalog(
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Course)
        .order_by(models.Course.id)
        .all()
    )

@app.post("/courses/", response_model=schemas.CourseResponse)
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(require_teacher_or_admin),
):
    new_course = models.Course(
        title=course.title,
        description=course.description
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


@app.get("/tasks/", response_model=list[schemas.TaskListResponse])
def get_tasks(
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Task).order_by(models.Task.id).all()


@app.get(
    "/tasks/progress/",
    response_model=list[schemas.TaskProgressResponse],
)
def get_task_progress(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    submissions = (
        db.query(models.TaskSubmission)
        .filter(models.TaskSubmission.user_id == current_user.id)
        .order_by(
            models.TaskSubmission.task_id,
            models.TaskSubmission.created_at.desc(),
            models.TaskSubmission.id.desc(),
        )
        .all()
    )
    latest_by_task = {}
    for submission in submissions:
        latest_by_task.setdefault(submission.task_id, submission)

    return [
        schemas.TaskProgressResponse(
            task_id=submission.task_id,
            submission_id=submission.id,
            status_id=submission.status_id,
            score=submission.score,
            total_tests=submission.total_tests,
            passed_tests=submission.passed_tests,
            error_count=submission.error_count,
        )
        for submission in latest_by_task.values()
    ]


@app.post("/tasks/", response_model=schemas.TaskResponse)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(require_teacher_or_admin),
):
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
def create_tasks_batch(
    course_id: int,
    payload: schemas.TaskBatchCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_teacher_or_admin),
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Nie znaleziono kursu.")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Batch jest pusty.")

    if len(payload.items) > BATCH_MAX_ITEMS:
        raise HTTPException(
            status_code=400,
            detail=f"Za duży batch. Maksymalna liczba zadań w jednym żądaniu to {BATCH_MAX_ITEMS}.",
        )

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
@app.post(
    "/submissions/",
    response_model=schemas.TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_submission(
    sub: schemas.TaskSubmissionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = db.query(models.Task).filter(models.Task.id == sub.task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania.")

    if not task.test_cases:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Zadanie nie ma przypadków testowych.",
        )

    new_submission = models.TaskSubmission(
        user_id=current_user.id,
        task_id=sub.task_id,
        source_code=sub.source_code,
        language_id=sub.language_id,
        status_id=1,
        total_tests=len(task.test_cases),
        attempt_number=1,
    )
    db.add(new_submission)
    db.flush()

    test_cases = [
        {
            "stdin": test_case.input_data,
            "expected_output": test_case.expected_output,
            "cpu_time_limit": task.time_limit,
            "memory_limit": task.memory_limit,
        }
        for test_case in task.test_cases
    ]
    try:
        judge0_submissions = enqueue_batch(
            source_code=sub.source_code,
            language_id=sub.language_id,
            test_cases=test_cases,
        )
    except Judge0Error as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    new_submission.judge0_token = judge0_submissions[0].token
    db.add_all(
        models.SubmissionTestResult(
            submission_id=new_submission.id,
            test_case_id=test_case.id,
            judge0_token=judge0_submission.token,
            status_id=judge0_submission.status_id or 1,
        )
        for test_case, judge0_submission in zip(
            task.test_cases,
            judge0_submissions,
        )
    )
    db.commit()
    db.refresh(new_submission)
    background_tasks.add_task(process_submission, new_submission.id)
    
    return new_submission


@app.get(
    "/submissions/{submission_id}",
    response_model=schemas.TaskSubmissionResponse,
)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    submission = (
        db.query(models.TaskSubmission)
        .filter(
            models.TaskSubmission.id == submission_id,
            models.TaskSubmission.user_id == current_user.id,
        )
        .first()
    )
    if submission is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono zgłoszenia.")

    if submission.status_id in (None, 1, 2):
        try:
            refresh_submission_from_judge0(submission)
            db.commit()
            db.refresh(submission)
        except (Judge0Error, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

    return submission