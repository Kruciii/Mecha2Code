from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from DB.database import Base # Pamiętaj o zaimportowaniu swojego Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Relacja do modułów: jeden kurs -> wiele modułów
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    order_index = Column(Integer, default=1)

    course = relationship("Course", back_populates="modules")
    # Relacja do zadań: jeden moduł -> wiele zadań
    tasks = relationship("Task", back_populates="module", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    time_limit = Column(Float, default=2.0) # w sekundach
    memory_limit = Column(Integer, default=128000) # w kilobajtach (128MB)

    module = relationship("Module", back_populates="tasks")
    test_cases = relationship("TestCase", back_populates="task", cascade="all, delete-orphan")
    submissions = relationship("TaskSubmission", back_populates="task")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    input_data = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, default=False)

    task = relationship("Task", back_populates="test_cases")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="student") # np. student, admin, teacher

    submissions = relationship("TaskSubmission", back_populates="user")


class TaskSubmission(Base):
    __tablename__ = "task_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Dane wysłane
    source_code = Column(Text, nullable=False)
    language_id = Column(Integer, default=54) # Domyślnie C++
    
    # Wyniki z Judge0
    judge0_token = Column(String(255))
    status_id = Column(Integer) # np. 3 to Accepted
    execution_time = Column(Float)
    memory_used = Column(Integer)
    
    # Telemetria z edytora i EDM
    attempt_number = Column(Integer, default=1)
    time_since_last_attempt = Column(Float)
    is_abandoned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacje zwrotne
    user = relationship("User", back_populates="submissions")
    task = relationship("Task", back_populates="submissions")