from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime

# ================= USER =================
class UserBase(BaseModel):
    email: EmailStr
    role: str = "student"

class UserCreate(UserBase):
    password: str # Zwykłe hasło, które API potem zahashuje

class UserResponse(UserBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# ================= COURSE =================
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# ================= TASK =================
class TaskResponse(BaseModel):
    id: int
    module_id: int
    title: str
    description: str
    time_limit: float
    memory_limit: int

    model_config = ConfigDict(from_attributes=True)

# ================= TASK SUBMISSION =================
class TaskSubmissionCreate(BaseModel):
    task_id: int
    source_code: str
    language_id: int = 54 # Domyślnie C++ (GCC 9.2.0)

class SubmissionTestResultResponse(BaseModel):
    id: int
    test_case_id: int
    judge0_token: str
    status_id: Optional[int]
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    execution_time: Optional[float] = None
    memory_used: Optional[int] = None
    passed: bool

    model_config = ConfigDict(from_attributes=True)

class TaskSubmissionResponse(BaseModel):
    id: int
    user_id: int
    task_id: int
    language_id: int
    status_id: Optional[int]
    score: Optional[float] = None
    total_tests: int = 0
    passed_tests: int = 0
    error_count: int = 0
    created_at: datetime
    is_abandoned: bool
    test_results: list[SubmissionTestResultResponse] = []

    model_config = ConfigDict(from_attributes=True)