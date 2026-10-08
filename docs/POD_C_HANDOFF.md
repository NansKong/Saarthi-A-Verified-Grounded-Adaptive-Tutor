# Pod C — Assessment & Learner Model (Handoff Doc)

This document explains **what Pod C is**, **what it needs from other pods**,
**what it gives back**, and **how it plugs into the whole system** — so any
teammate can pick it up and continue without asking.

---

## 1. What this pod is, in one line

Pod C is the **tutor's brain**: it decides *what to ask the student* and
remembers *what the student knows*. Everything else (the graph, the dashboard)
either feeds it or displays its results.

---

## 2. Where Pod C sits in the architecture

```
STUDENT MATERIAL (PDF, slides, video)
        |
MULTIMODAL EXTRACTION            <- Pod A
        |
KNOWLEDGE GRAPH                  <- Pod B
(concepts, prerequisites, evidence)
        |
RAG RETRIEVAL                    <- Pod B
        |
   +----------------------------+
   |   QUIZ  -> Generator       |   <-- Pod C  (assessment half)
   |            Verifier        |   <-- Pod C
   |       Verified Question    |   <-- Pod C  OUTPUT
   +----------------------------+
        |
STUDENT ANSWER (from the dashboard)
        |
LEARNER MODEL (BKT)              <-- Pod C  (learner half)
        |
UPDATED MASTERY                  <-- Pod C  OUTPUT
        |
NEXT BEST CONCEPT                <-- Pod C  OUTPUT
        |
NEXT QUESTION  (loops back into the generator)
```

Pod C owns the middle of the flow: the quiz branch and the learner model. It
receives the graph from Pod B, talks to the student through Pod D, and feeds
results back into itself to pick the next question.

---

## 3. What Pod C NEEDS from other pods (INPUTS)

| Comes from | What it is | Why Pod C needs it |
| ---------- | ---------- | ------------------ |
| **Pod B** (graph) | `ConceptNode` objects — concepts + prerequisites | To know what topics exist and what order they should be learned in |
| **Pod B** (graph) | `ContentUnit` objects — the real source text/slides per concept | So the generator writes questions grounded in real material |
| **Pod D** (dashboard) | The student's answers (sent to `POST /answer`) | To grade, update mastery, and choose the next question |
| **Environment** | `GROQ_API_KEY` | The generator (writes questions) |
| **Environment** | `GEMINI_API_KEY` | The verifier (checks questions) and the optional embeddings |

**Important:** right now Pod C uses **fake** versions of the Pod B data, in
`mock_data.py` (6 concepts, 12 questions, 6 content units). When Pod B's real
graph is ready, replace the `get_concepts()` / `get_content_units()` functions
with calls to Pod B's output. **Nothing else changes** — that is the whole point
of the frozen data contract in section 5.

---

## 4. What Pod C GIVES to other pods (OUTPUTS)

| Output | Who uses it | What's in it |
| ------ | ----------- | ------------ |
| **Verified `Question`** | Pod D (shows it to the student) | Question text, options, answer, topic, source location, difficulty, `verified` flag |
| **`LearnerState`** | Pod D (dashboard bars) | `student_id`, and the mastery map `{concept_id: P(L)}` across all concepts |
| **Next-concept recommendation** | Pod C itself (loops back) | The concept the student should be asked about next |
| **Post-assessment report** | Pod D (results screen) | Weak topics, per-answer feedback with citations, likely misconceptions |

The **loop** is the important part: the mastery output does not just go to the
dashboard, it also feeds back into the generator to pick the next question.
That loop is what makes the system adaptive instead of random.

---

## 5. The data contract (FREEZE THESE — do not change without telling the team)

These four shapes are what all four pods agreed on. Pod C **receives** the
first two and **sends** the `Question` and the `LearnerState`.

```
// 1. ContentUnit  - one chunk of source material
{ unit_id, source_id, source_type: 'video'|'pdf'|'slides',
  location: { page | slide | timestamp },
  text, image_caption?, embedding, topic_ids[] }

// 2. ConceptNode  - one idea in the graph
{ concept_id, name, topic, prerequisites: [concept_id],
  evidence_units: [unit_id] }

// 3. Question  - one assessment item
{ q_id, concept_id, topic, source_location, difficulty: 1-5,
  type: 'mcq'|'short'|'numeric', stem, options?, answer,
  verified: bool, verifier_agreement, embedding }

// 4. LearnerState  - the student's mastery across all concepts
{ student_id, masteries: { concept_id: P(L) }, updated_at }
```

These are implemented in the frozen `src/schemas/models.py` module. Pod C
imports those models directly rather than redefining them. Do not change these
shapes without full team consensus.

---

## 6. The HTTP API (how Pod D connects)

Run the service, then Pod D calls these endpoints over HTTP:

| Method & path | Purpose |
| ------------- | ------- |
| `GET  /health` | Is the service alive? |
| `GET  /concepts` | The concept graph Pod C is working with |
| `POST /quiz` | Build an adaptive quiz for a student |
| `POST /answer` | Grade one answer, update mastery, return the next concept |
| `GET  /mastery/{student_id}` | The mastery board (for the dashboard bars) |
| `GET  /report/{student_id}` | The post-assessment report |
| `POST /generate` | Generate + verify + de-dup one new question |

Example — build a quiz:

```
POST /quiz
{ "student_id": "s1", "size": 5 }
```

Example — answer a question (the correct answer is hidden from the quiz, so the
server grades it):

```
POST /answer
{ "student_id": "s1", "q_id": "q6", "answer": "Opposite to the gradient" }

-> { "correct": true, "correct_answer": "Opposite to the gradient",
     "concept_id": "gradient_descent", "new_mastery": 0.71,
     "next_concept": "chain_rule", "next_difficulty": 2 }
```

---

## 7. The files in this pod

| File | Job |
| ---- | --- |
| `src/schemas/models.py` | The frozen data contract (section 5) |
| `mock_data.py` | Fake concepts, questions, and source text — stand-in until Pod B is ready |
| `bkt.py` | The learner model: per-concept mastery, updated after every answer (+ forgetting curve) |
| `adaptive.py` | Picks the next concept and the difficulty |
| `generator.py` | Groq writes one question from a concept's source text |
| `verifier.py` | Gemini checks the question independently (blind); sets `verified` |
| `sympy_check.py` | The third check for numeric questions: SymPy computes the answer |
| `dedup.py` | Stops the same question appearing twice |
| `report.py` | The post-assessment report (feedback, weak topics, misconceptions) |
| `service.py` | FastAPI service — exposes all of the above over HTTP |
| `llm_connect.py` | Tiny test that the AI connections work |
| `run_demo.py` | Shows the learner model working |

### Where these files live in the repo

The main README fixes the repo layout. Pod C's code belongs under `src/`, split
into two folders, with the shared contract in `src/schemas/models.py`:

```
sarthi/
├── src/
│   ├── schemas/
│   │   └── models.py            <- was schemas.py
│   ├── assessment/              [Pod C]
│   │   ├── generator.py
│   │   ├── verifier.py
│   │   ├── sympy_check.py
│   │   └── dedup.py
│   ├── learner_model/           [Pod C]
│   │   ├── bkt.py
│   │   ├── adaptive.py
│   │   └── report.py
│   ├── api/                     [Pod D]  <- service.py goes here
│   ├── eval/                    [Pod D]  <- simulate.py goes here
│   ├── ingestion/               [Pod A]  (not ours)
│   ├── graph/                   [Pod B]  (not ours)
│   ├── retrieval/               [Pod B]  (not ours)
│   └── mock_data.py             (temporary fixture; delete when Pod B is ready)
├── scripts/
│   ├── run_demo.py
│   └── llm_connect.py
├── docs/
│   └── POD_C_HANDOFF.md
├── .env.example
├── .gitignore
└── README.md
```

**Where each current file goes:**

| Current file | New location |
| ------------ | ------------ |
| `schemas.py` | `src/schemas/models.py` |
| `generator.py`, `verifier.py`, `sympy_check.py`, `dedup.py` | `src/assessment/` |
| `bkt.py`, `adaptive.py`, `report.py` | `src/learner_model/` |
| `service.py` | `src/api/` (Pod D's integration layer) |
| `simulate.py` | `src/eval/` (Pod D's evaluation layer) |
| `mock_data.py` | `src/mock_data.py` (temporary shared fixture) |
| `run_demo.py`, `llm_connect.py` | `scripts/` |
| `POD_C_HANDOFF.md` | `docs/` |

**After moving, fix the imports** — every module needs its path updated:

| Before | After |
| ------ | ----- |
| `from schemas import X` | `from src.schemas.models import X` |
| `from mock_data import X` | `from src.mock_data import X` |
| `from bkt import X` | `from src.learner_model.bkt import X` |
| `from generator import X` | `from src.assessment.generator import X` |

Two housekeeping notes: add an empty `__init__.py` to each `src/` subfolder so
Python treats them as packages, and keep `__pycache__/` and `.env` out of git
(in `.gitignore`).

---

## 8. How to run and test

Install what's needed:

```
pip install fastapi uvicorn groq google-genai
```

Set the keys (Windows):

```
set GROQ_API_KEY=your_key
set GEMINI_API_KEY=your_key
```

Run the individual pieces from the repository root:

```
python -m scripts.run_demo                         # the learner model
python -m src.learner_model.adaptive              # builds the diagnostic
python -m src.assessment.generator                # write one question
python -m src.assessment.verifier                 # check one question
python -m src.assessment.sympy_check               # compute numeric answers
python -m src.assessment.dedup                     # de-duplication
python -m src.learner_model.report                 # the report
```

Run the whole thing as a service:

```
uvicorn src.api.service:app --reload
# then open http://127.0.0.1:8000/docs
```

Everything also runs **without keys** in a dry-run mode, so you can test the
flow before the API keys are set.

---

## 9. Status: done vs. left

**Done:**
- Learner model (BKT) with mastery updates and a forgetting curve
- Adaptive next-question selector + 8-question diagnostic builder
- Question generator (Groq) + verifier (Gemini) + SymPy numeric check
- De-duplication and the post-assessment report
- `LearnerState` output shape (aligned with the team's frozen contract)
- FastAPI service exposing all of it

**Left (needs the team):**
- **Swap the mock data** for Pod B's real `ConceptNode` + `ContentUnit` output.
- **Simulated-student evaluation** — run weak/average/strong profiles through
  the learner model and report the adaptive-vs-random gain (this is the
  "measurable personalization" the rubric wants; implemented in
  `src/eval/simulate.py`, with final reporting owned by Pod D).
- **Wire the dashboard** (Pod D) to the endpoints in section 6.

---

## 10. Quick checklist for whoever picks this up

1. Do the four schemas in `src/schemas/models.py` still match Pod B and Pod D? If not, fix
   them first — everything else depends on them.
2. Replace `mock_data.py` with Pod B's real output.
3. Run `uvicorn src.api.service:app` and confirm `/docs` loads.
4. Point Pod D's dashboard at the endpoints in section 6.
5. Run the simulated-student evaluation and record the adaptive-vs-random gap.

---

*Pod C — Assessment & Learner Model. Part of the Saarthi project (Multimodal AI
Hackathon 2026, Track D).*
