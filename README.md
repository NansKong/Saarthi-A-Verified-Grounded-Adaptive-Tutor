# Saarthi: A Verified-Grounded Adaptive Tutor
> **Multimodal AI Hackathon 2026 · Track D: Personalized Tutoring & Adaptive Learning**

Saarthi is an AI study companion that ingests multimodal course materials (textbooks, slides, lecture videos), constructs an evidence-grounded prerequisite knowledge graph, generates independently-verified assessment items, and personalizes the student's learning journey using Bayesian Knowledge Tracing (BKT).

---

## 🏛️ Team Architecture & Pod Division
To ensure **zero overlap and inconsistency** across our 4 team members, the repository is split into 4 decoupled pods coordinated via frozen schemas:

```
src/
├── schemas/           # Single Source of Truth (Frozen Data Contract)
│   ├── models.py      # ContentUnit, ConceptNode, Question, LearnerState
│   └── __init__.py
├── ingestion/         # [Pod A / Member A] Multimodal Parsers, Whisper, Vision Captioning
├── graph/             # [Pod B / Member B] Concept Graph DAG (NetworkX), Prerequisite Mining
├── retrieval/         # [Pod B / Member B] Hybrid Search (BM25 + Dense), Citations, Refusal
├── assessment/        # [Pod C / Member C] Quiz Generator, Dual-LLM Verifier, SymPy Validator
├── learner_model/     # [Pod C / Member C] BKT Engine, Diagnostic Test, Prerequisite Walk
├── api/               # [Pod D / Member D] FastAPI Service Layer (Integration Hub)
├── ui/                # [Pod D / Member D] Student Dashboard & Grounded Chatbot UI
└── eval/              # [Pod D / Member D] RAGAS Harness & Simulated Student Benchmarking
```

### Pod Ownership Matrix
| Pod | Owner | Core Responsibilities | Input Schema | Output Schema |
| :--- | :--- | :--- | :--- | :--- |
| **Pod A** | Member A | PDF/PPTX parsing, Whisper timestamps, Vision diagram captioning, chunking | Raw Files | `ContentUnit` |
| **Pod B** | Member B | Concept/prerequisite graph, Hybrid search, reranking, source citation chips, refusal logic | `ContentUnit` | `ConceptNode` + Grounded Citations |
| **Pod C** | Member C | Assessment generator, Dual-LLM verifier, SymPy check, BKT engine, adaptive next-step logic | `ConceptNode` | `Question`, `LearnerState` |
| **Pod D** | Member D | UI dashboard, FastAPI integration, RAGAS benchmark, simulated student ablation bench | All Schemas | Full Web App & Evaluation Report |

---

## 🔒 Shared Data Contract (`src/schemas/models.py`)
1. **`ContentUnit`**: Chunk of course material with exact slide/page/timestamp coordinates and image captions.
2. **`ConceptNode`**: Conceptual unit with prerequisite links and supporting evidence units.
3. **`Question`**: Assessment item tagged with source, difficulty, verification badge, and mathematical correctness.
4. **`LearnerState`**: Concept mastery probabilities $P(L_t)$ maintained via Bayesian Knowledge Tracing.

---

## 🔄 Collaboration Guidelines
1. **Always fetch before starting**: Run `git fetch origin` to check for incoming changes from teammates.
2. **Respect Pod Boundaries**: Work only within your assigned module directory.
3. **Do not modify schemas**: `src/schemas/models.py` is frozen; changes require full team consensus.
