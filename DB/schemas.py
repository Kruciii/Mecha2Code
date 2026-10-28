from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime

# ================= USER =================
class UserBase(BaseModel):
    email: EmailStr
    semester: int = Field(ge=1, le=10)
    start_year: int = Field(ge=2000, le=2100)
    major: Literal["mechatro", "AIR"]

class UserCreate(UserBase):
    password: str # Zwykłe hasło, które API potem zahashuje
    registration_secret: str

class UserResponse(UserBase):
    id: int
    role: str
    
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# ================= COURSE =================
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    language: str = "cpp"
    language_id: int = 54

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
    tags: str = "łatwe" 

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
    tags: str = "łatwe" 

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

class CourseTaskResponse(BaseModel):
    id: int
    title: str
    description: str
    time_limit: float
    memory_limit: int
    tags: str = "łatwe" 

    model_config = ConfigDict(from_attributes=True)

class ModuleCatalogResponse(BaseModel):
    id: int
    title: str
    order_index: int
    tasks: list[CourseTaskResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class CourseCatalogResponse(CourseResponse):
    modules: list[ModuleCatalogResponse] = Field(default_factory=list)

# ================= TASK LIST =================
class TaskListResponse(BaseModel):
    id: int
    module_id: int
    title: str
    description: str
    time_limit: float
    memory_limit: int
    tags: str = "łatwe" 

    model_config = ConfigDict(from_attributes=True)

class TaskProgressResponse(BaseModel):
    task_id: int
    submission_id: int
    status_id: Optional[int]
    score: Optional[float] = None
    total_tests: int = 0
    passed_tests: int = 0
    error_count: int = 0

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
    test_results: list[SubmissionTestResultResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)