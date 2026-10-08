"""
service.py  --  Pod C as a web service (FastAPI).

This wraps everything your pod does behind HTTP endpoints, so Pod D's
dashboard can call it. Start it with:

    uvicorn src.api.service:app
    # then open http://127.0.0.1:8000/docs  to click through the endpoints

Or with the standard runner:
    uvicorn src.api.service:app --reload

State is kept in memory (fine for a hackathon). Two students, a question bank,
and each student's answers live in dicts below.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.mock_data import (
    get_concepts,
    get_questions,
    get_content_units,
    get_question_concept_id,
)
from src.learner_model.bkt import LearnerModel
from src.learner_model.adaptive import (
    build_quiz,
    select_next_concept,
    choose_difficulty,
)
from src.learner_model.report import build_report
from src.assessment.generator import (
    build_source_text,
    generate_question,
    select_groq_model,
    source_location,
)
from src.assessment.verifier import verify_question, make_gemini_client, answers_match
from src.assessment.dedup import find_duplicate

app = FastAPI(title="Saarthi - Pod C (Assessment & Learner Model)")

# ---------- in-memory state ----------
CONCEPTS = get_concepts()
CONCEPTS_BY_ID = {c.concept_id: c for c in CONCEPTS}
UNITS = get_content_units()
QUESTION_BANK = {q.q_id: q for q in get_questions()}   # q_id -> Question
STUDENTS = {}      # student_id -> LearnerModel
SESSIONS = {}      # student_id -> list of (question, answer, correct)
USED_QIDS = {}     # student_id -> set of q_ids already asked


def get_student(student_id):
    if student_id not in STUDENTS:
        STUDENTS[student_id] = LearnerModel([c.concept_id for c in CONCEPTS])
        SESSIONS[student_id] = []
        USED_QIDS[student_id] = set()
    return STUDENTS[student_id]


def q_to_dict(q, include_answer=False):
    d = {
        "q_id": q.q_id, "concept_id": get_question_concept_id(q), "topic": q.topic,
        "source_location": q.source_location, "difficulty": q.difficulty,
        "type": q.type, "stem": q.stem, "options": q.options,
        "verified": q.verified,
    }
    if include_answer:
        d["answer"] = q.answer
    return d


# ---------- request models ----------
class QuizRequest(BaseModel):
    student_id: str
    size: int = 5


class AnswerRequest(BaseModel):
    student_id: str
    q_id: str
    answer: str


class GenerateRequest(BaseModel):
    student_id: str
    concept_id: str


# ---------- endpoints ----------
@app.get("/health")
def health():
    return {"status": "ok", "concepts": len(CONCEPTS), "questions": len(QUESTION_BANK)}


@app.get("/concepts")
def concepts():
    return [{"concept_id": c.concept_id, "name": c.name, "topic": c.topic,
             "prerequisites": c.prerequisites} for c in CONCEPTS]


@app.post("/quiz")
def quiz(req: QuizRequest):
    """Build an adaptive quiz. Answers are hidden -- grading happens server-side."""
    student = get_student(req.student_id)
    qs = build_quiz(CONCEPTS, student.all_masteries(), list(QUESTION_BANK.values()),
                    used_ids=USED_QIDS[req.student_id], size=req.size)
    for q in qs:
        USED_QIDS[req.student_id].add(q.q_id)
    return {"student_id": req.student_id,
            "questions": [q_to_dict(q, include_answer=False) for q in qs]}


@app.post("/answer")
def answer(req: AnswerRequest):
    """Grade one answer, update mastery, and say what to ask next."""
    student = get_student(req.student_id)
    q = QUESTION_BANK.get(req.q_id)
    if q is None:
        raise HTTPException(status_code=404, detail=f"unknown question {req.q_id}")

    correct = answers_match(req.answer, q.answer, q.type)
    concept_id = get_question_concept_id(q)
    new_mastery = student.observe(concept_id, correct)
    SESSIONS[req.student_id].append((q, req.answer, correct))

    nxt = select_next_concept(CONCEPTS, student.all_masteries())
    return {
        "correct": correct,
        "correct_answer": q.answer,
        "concept_id": concept_id,
        "new_mastery": round(new_mastery, 4),
        "next_concept": nxt,
        "next_difficulty": choose_difficulty(student.mastery(nxt)),
    }


@app.get("/mastery/{student_id}")
def mastery(student_id: str):
    student = get_student(student_id)
    board = [{"concept_id": c.concept_id, "name": c.name,
              "mastery": round(student.mastery(c.concept_id), 4)} for c in CONCEPTS]
    board.sort(key=lambda x: x["mastery"])
    return {"student_id": student_id, "board": board}


@app.get("/report/{student_id}")
def report(student_id: str):
    student = get_student(student_id)
    text = build_report(SESSIONS[student_id], student, CONCEPTS)
    return {"student_id": student_id, "report": text}


@app.post("/generate")
def generate(req: GenerateRequest):
    """Generate + verify + de-duplicate ONE new question, and add it to the bank."""
    import os
    concept = CONCEPTS_BY_ID.get(req.concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail=f"unknown concept {req.concept_id}")

    src = build_source_text(concept, UNITS)
    loc = source_location(concept, UNITS)

    groq_client = None
    if os.environ.get("GROQ_API_KEY"):
        try:
            from groq import APIConnectionError, APIStatusError, Groq
            groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
            groq_model = select_groq_model(groq_client)
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="The 'groq' package is missing. Run: pip install groq",
            )
        except (APIStatusError, APIConnectionError, ValueError) as error:
            raise HTTPException(status_code=502, detail=f"Groq setup failed: {error}")
    else:
        groq_model = None

    question, _ = generate_question(
        concept, src, loc, groq_client, groq_model
    )

    gemini_client = None
    if os.environ.get("GEMINI_API_KEY"):
        gemini_client = make_gemini_client(os.environ["GEMINI_API_KEY"])
    question, gemini_answer, _ = verify_question(question, src, gemini_client)

    dup, sim = find_duplicate(question.stem, [q.stem for q in QUESTION_BANK.values()])
    if not question.verified:
        return {"status": "rejected", "reason": "verifier disagreed", "question": q_to_dict(question, True)}
    if dup:
        return {"status": "duplicate", "reason": f"too close to: {dup}", "similarity": round(sim, 2)}
    QUESTION_BANK[question.q_id] = question
    return {"status": "added", "question": q_to_dict(question, True)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)