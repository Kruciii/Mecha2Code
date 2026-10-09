from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class UserCreate(BaseModel):
    name: str
    user_type: str = "student"
    date_of_birth: Optional[date]= None

class UserResponse(BaseModel):
    id: int 
    name: str
    user_type: str
    class Config:
        from_attributes = True


class TestResultResponse(BaseModel):
    test_id: int
    content: str  
    answer: str   

    class Config:
        from_attributes = True

class CommitCreate(BaseModel):
    user_id : int
    excercise_id : int 
    source_code : str

class CommitResponse(BaseModel):
    id : int
    user_id : int
    excercise_id : int 
    source_code : str
    #code generated
    valid : bool
    start_time : datetime
    end_time : datetime
    compiler_error_count : int
    test_results: List[TestResultResponse] = []



class ExcerciseResponse(BaseModel):
    id: int
    difficulty: str
    description: str

