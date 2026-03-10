from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime

from app.core.database import get_db
from app.models.schemas import (
    SessionCreate, SessionOut, AnswerPayload, AnswerResult,
    QuestionOut, ResponseRecord, StudyPlan,
)
from app.services.adaptive import update_ability, select_next_question
from app.services.llm import generate_study_plan, _identify_weak_topics

router = APIRouter()


# ── Helper ────────────────────────────────────────────────────────────────────

def _q_out(q: dict) -> QuestionOut:
    return QuestionOut(
        id=str(q["_id"]),
        text=q["text"],
        options=q["options"],
        difficulty=q["difficulty"],
        topic=q["topic"],
        tags=q.get("tags", []),
    )


# ── Start Session ─────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionOut, status_code=201)
async def create_session(payload: SessionCreate):
    """Create a new adaptive testing session."""
    db = get_db()
    doc = {
        "student_name": payload.student_name,
        "ability": 0.5,
        "question_count": 0,
        "max_questions": payload.max_questions,
        "responses": [],
        "asked_question_ids": [],
        "complete": False,
        "created_at": datetime.utcnow(),
    }
    result = await db["sessions"].insert_one(doc)
    return SessionOut(
        session_id=str(result.inserted_id),
        student_name=payload.student_name,
        ability=0.5,
        question_count=0,
        max_questions=payload.max_questions,
        complete=False,
    )


# ── Get Next Question ─────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/next-question", response_model=QuestionOut)
async def next_question(session_id: str):
    """
    Return the next adaptively selected question for this session.
    Selects the question whose difficulty is closest to the student's current ability.
    """
    db = get_db()
    session = await db["sessions"].find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["complete"]:
        raise HTTPException(status_code=400, detail="Session is already complete")

    all_questions = await db["questions"].find().to_list(length=500)
    chosen = select_next_question(
        ability=session["ability"],
        questions=all_questions,
        asked_ids=session["asked_question_ids"],
    )
    if not chosen:
        raise HTTPException(status_code=404, detail="No more questions available")

    return _q_out(chosen)


# ── Submit Answer ─────────────────────────────────────────────────────────────

@router.post("/sessions/submit-answer", response_model=AnswerResult)
async def submit_answer(payload: AnswerPayload):
    """
    Submit a student's answer.
    - Updates ability via 1PL IRT
    - Records response
    - Marks session complete after max_questions
    """
    db = get_db()

    # Validate session
    try:
        s_oid = ObjectId(payload.session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session_id")
    session = await db["sessions"].find_one({"_id": s_oid})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["complete"]:
        raise HTTPException(status_code=400, detail="Session is already complete")

    # Validate question
    try:
        q_oid = ObjectId(payload.question_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid question_id")
    question = await db["questions"].find_one({"_id": q_oid})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Score answer
    correct = payload.selected_answer.strip().upper() == question["correct_answer"].strip().upper()

    # IRT ability update
    new_ability = update_ability(
        ability=session["ability"],
        difficulty=question["difficulty"],
        correct=correct,
    )

    # Build response record
    response_record = {
        "question_id": payload.question_id,
        "topic": question["topic"],
        "difficulty": question["difficulty"],
        "selected_answer": payload.selected_answer,
        "correct": correct,
        "timestamp": datetime.utcnow(),
    }

    new_count = session["question_count"] + 1
    is_complete = new_count >= session["max_questions"]

    # Update session in DB
    await db["sessions"].update_one(
        {"_id": s_oid},
        {
            "$set": {
                "ability": new_ability,
                "question_count": new_count,
                "complete": is_complete,
            },
            "$push": {
                "responses": response_record,
                "asked_question_ids": payload.question_id,
            },
        },
    )

    # Find next question ID (if session not done)
    next_q_id = None
    if not is_complete:
        all_questions = await db["questions"].find().to_list(length=500)
        asked = session["asked_question_ids"] + [payload.question_id]
        nxt = select_next_question(new_ability, all_questions, asked)
        if nxt:
            next_q_id = str(nxt["_id"])

    return AnswerResult(
        correct=correct,
        correct_answer=question["correct_answer"],
        new_ability=new_ability,
        next_question_id=next_q_id,
        session_complete=is_complete,
    )


# ── Get Session Status ────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(session_id: str):
    """Get current state of a session."""
    db = get_db()
    session = await db["sessions"].find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut(
        session_id=str(session["_id"]),
        student_name=session["student_name"],
        ability=session["ability"],
        question_count=session["question_count"],
        max_questions=session["max_questions"],
        complete=session["complete"],
    )


# ── Generate Study Plan ───────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/study-plan", response_model=StudyPlan)
async def get_study_plan(session_id: str):
    """
    Generate a personalized 3-step study plan using the Anthropic LLM.
    Only available once the session is complete.
    """
    db = get_db()
    session = await db["sessions"].find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session["complete"]:
        raise HTTPException(status_code=400, detail="Session is not yet complete")

    responses = [ResponseRecord(**r) for r in session["responses"]]
    correct = sum(1 for r in responses if r.correct)
    score_pct = (correct / len(responses) * 100) if responses else 0.0
    weak_topics = _identify_weak_topics(responses)

    try:
        steps = generate_study_plan(
            student_name=session["student_name"],
            final_ability=session["ability"],
            responses=responses,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    return StudyPlan(
        student_name=session["student_name"],
        final_ability=session["ability"],
        total_questions=session["question_count"],
        score=round(score_pct, 1),
        weak_topics=weak_topics,
        steps=steps,
    )
