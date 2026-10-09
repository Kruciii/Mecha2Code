from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db, engine
import models
import schemas

app = FastAPI(title="MechaCode API")

@app.get("/users/",response_model=list[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users


@app.post("/users/",response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate , db: Session = Depends(get_db)):
    new_user = models.User(
        name = user.name,
        user_type = user.user_type,
        date_of_birth = user.date_of_birth
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# @app.get("/excercises/",response_model=schemas.ExcerciseResponse)
# def get_excersise(db: Session = Depends(get_db)):
#   exercises = 