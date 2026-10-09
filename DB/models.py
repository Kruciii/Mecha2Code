from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from DB.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_type = Column(String)  # np. 'admin', 'student'
    date_of_birth = Column(Date)
    university = Column(String)
    degree = Column(String)
    year = Column(Integer)

class StudentInCourse(Base):
    __tablename__ = "student_in_course"

    id = Column(Integer, primary_key= True,index = True)
    EnrolledDate =Column(Date)


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    tags = Column(String)
    difficulty = Column(String)
    description = Column(Text)


class Excercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key= True,index=True)
    difficulty = Column(String)
    description = Column(Text)



class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id")) 
    content = Column(Text) 
    answer = Column(Text)  

    exercise = relationship("Exercise", back_populates="tests")
    commit_tests = relationship("TestsInCommits", back_populates="test")

class Commit(Base):
    __tablename__ = "commits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id")) 
    source_code = Column(Text, nullable=False) 
    
    valid = Column(Boolean, default=False)
    start_time = Column(DateTime, default=datetime.now())
    end_time = Column(DateTime)
    
    compiler_error_count = Column(Integer, default=0)

    user = relationship("User", back_populates="commits")
    exercise = relationship("Exercise", back_populates="commits")
    test_results = relationship("TestsInCommits", back_populates="commit")


class TestsInCommits(Base):
    __tablename__ = "tests_in_commits"
    
    id = Column(Integer, primary_key=True, index=True)
    commit_id = Column(Integer, ForeignKey("commits.id"))
    test_id = Column(Integer, ForeignKey("tests.id"))
    content = Column(Text) 
    answer = Column(Text)  

    commit = relationship("Commit", back_populates="test_results")
    test = relationship("Test", back_populates="commit_tests")