from pydantic import BaseModel, ConfigDict, EmailStr, Field
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

# ================= COURSE =================
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# ================= TEST CASE =================
class TestCaseBase(BaseModel):
    input_data: str
    expected_output: str
    is_hidden: bool = False

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseResponse(TestCaseBase):
    id: int
    task_id: int

    model_config = ConfigDict(from_attributes=True)

# ================= TASK =================
class TaskBase(BaseModel):
    module_id: int
    title: str
    description: str
    time_limit: float = 2.0
    memory_limit: int = 128000

class TaskCreate(TaskBase):
    test_cases: List[TestCaseCreate] = Field(default_factory=list)

class TaskResponse(TaskBase):
    id: int
    test_cases: List[TestCaseResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# ================= TASK BATCH IMPORT =================
class TaskBatchItemTask(BaseModel):
    title: str
    description: str
    time_limit: float = 2.0
    memory_limit: int = 128000

class TaskBatchItem(BaseModel):
    module_id: int
    task: TaskBatchItemTask
    test_cases: List[TestCaseCreate] = Field(default_factory=list)

class TaskBatchCreateRequest(BaseModel):
    items: List[TaskBatchItem] = Field(default_factory=list, max_length=100)
    dry_run: bool = False

class TaskBatchCreateResponse(BaseModel):
    course_id: int
    created_tasks: int
    created_test_cases: int
    task_ids: List[int] = Field(default_factory=list)
    dry_run: bool
    message: str

# ================= TASK SUBMISSION =================
class TaskSubmissionCreate(BaseModel):
    user_id: int
    task_id: int
    source_code: str
    language_id: int = 54 # Domyślnie C++ (GCC 9.2.0)

class TaskSubmissionResponse(BaseModel):
    id: int
    user_id: int
    task_id: int
    language_id: int
    status_id: Optional[int]
    created_at: datetime
    is_abandoned: bool

    model_config = ConfigDict(from_attributes=True)