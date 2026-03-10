from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.core.database import get_db
from app.models.schemas import QuestionOut

router = APIRouter()


def _serialize_question(q: dict) -> QuestionOut:
    return QuestionOut(
        id=str(q["_id"]),
        text=q["text"],
        options=q["options"],
        difficulty=q["difficulty"],
        topic=q["topic"],
        tags=q.get("tags", []),
    )


@router.get("/questions", response_model=list[QuestionOut])
async def list_questions():
    """List all questions (without correct answers)."""
    db = get_db()
    questions = await db["questions"].find().to_list(length=100)
    return [_serialize_question(q) for q in questions]


@router.get("/questions/{question_id}", response_model=QuestionOut)
async def get_question(question_id: str):
    """Get a single question by ID."""
    db = get_db()
    try:
        oid = ObjectId(question_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid question ID format")

    q = await db["questions"].find_one({"_id": oid})
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return _serialize_question(q)
