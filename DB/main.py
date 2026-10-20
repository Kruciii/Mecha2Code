import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import get_db, engine
import models
import schemas
from judge0_client import Judge0Error, enqueue_batch, get_batch_results

# Jeśli tabele jeszcze nie istnieją, ta linijka je stworzy (przydatne przed ustawieniem Alembica)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MechaCode API")

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
@app.get("/tasks/", response_model=list[schemas.TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    return db.query(models.Task).order_by(models.Task.id).all()


# ----------------- SUBMISSIONS -----------------
@app.post(
    "/submissions/",
    response_model=schemas.TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_submission(
    sub: schemas.TaskSubmissionCreate,
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

    pending_results = [
        result for result in submission.test_results
        if result.status_id in (None, 1, 2)
    ]
    if pending_results:
        try:
            judge_results = get_batch_results(
                [result.judge0_token for result in pending_results]
            )
        except Judge0Error as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

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

    if submission.test_results and all(
        result.status_id not in (None, 1, 2)
        for result in submission.test_results
    ):
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

    db.commit()
    db.refresh(submission)
    return submission