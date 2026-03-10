from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ── Question Models ──────────────────────────────────────────────────────────

class QuestionBase(BaseModel):
    text: str
    options: List[str]           # e.g. ["A) ...", "B) ...", "C) ...", "D) ..."]
    correct_answer: str          # e.g. "A"
    difficulty: float = Field(..., ge=0.1, le=1.0)
    topic: str                   # e.g. "Algebra", "Vocabulary"
    tags: List[str] = []


class QuestionInDB(QuestionBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class QuestionOut(BaseModel):
    """Sent to the student — no correct_answer exposed."""
    id: str
    text: str
    options: List[str]
    difficulty: float
    topic: str
    tags: List[str]


# ── Response Models ──────────────────────────────────────────────────────────

class AnswerPayload(BaseModel):
    session_id: str
    question_id: str
    selected_answer: str         # e.g. "B"


class AnswerResult(BaseModel):
    correct: bool
    correct_answer: str
    new_ability: float
    next_question_id: Optional[str] = None
    session_complete: bool = False


# ── Session Models ───────────────────────────────────────────────────────────

class ResponseRecord(BaseModel):
    question_id: str
    topic: str
    difficulty: float
    selected_answer: str
    correct: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserSession(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    student_name: str
    ability: float = 0.5         # theta: estimated proficiency [0, 1]
    question_count: int = 0
    max_questions: int = 10
    responses: List[ResponseRecord] = []
    asked_question_ids: List[str] = []
    complete: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class SessionCreate(BaseModel):
    student_name: str
    max_questions: int = 10


class SessionOut(BaseModel):
    session_id: str
    student_name: str
    ability: float
    question_count: int
    max_questions: int
    complete: bool


# ── Study Plan Models ────────────────────────────────────────────────────────

class StudyPlan(BaseModel):
    student_name: str
    final_ability: float
    total_questions: int
    score: float                 # percent correct
    weak_topics: List[str]
    steps: List[Dict[str, Any]]  # 3-step plan from LLM
