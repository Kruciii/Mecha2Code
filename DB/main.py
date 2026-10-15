from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine
import models
import schemas
import os
import httpx


# Jeśli tabele jeszcze nie istnieją, ta linijka je stworzy (przydatne przed ustawieniem Alembica)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MechaCode API")


JUDGE0_URL = os.getenv(
    "JUDGE0_URL",
).rstrip("/")

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


# ----------------- SUBMISSIONS -----------------

@app.post("/submissions/", response_model=schemas.TaskSubmissionResponse)
def create_submission(
    sub: schemas.TaskSubmissionCreate,
    db: Session = Depends(get_db),
):
    new_submission = models.TaskSubmission(
        user_id=sub.user_id,
        task_id=sub.task_id,
        source_code=sub.source_code,
        language_id=sub.language_id,
        status_id=1,
        attempt_number=1,
    )

    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    try:
        response = httpx.post(
            f"{JUDGE0_URL}/submissions",
            params={
                "base64_encoded": "false",
                "wait": "false",
            },
            json={
                "source_code": sub.source_code,
                "language_id": sub.language_id,
                "stdin": "",
            },
            timeout=15.0,
        )

        response.raise_for_status()
        judge0_data = response.json()
        token = judge0_data["token"]

    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Nie udało się wysłać zgłoszenia do Judge0",
                "submission_id": new_submission.id,
            },
        ) from exc

    new_submission.judge0_token = token

    db.commit()
    db.refresh(new_submission)

    return new_submission