# Saarthi Project Instructions & Collaboration Protocol

## 1. Remote Repository & Startup Checklist
- **Repository URL**: `https://github.com/NansKong/Saarthi-A-Verified-Grounded-Adaptive-Tutor.git`
- **MANDATORY STARTUP RULE**:
  At the beginning of every session or task:
  1. Check remote status: `git fetch origin`
  2. Verify current branch status and check for incoming changes from collaborators: `git status` or `git log origin/main -n 5`
  3. Avoid overwrite conflicts by ensuring clean synchronization.

---

## 2. Team Split & Zero-Overlap Isolation (4-Pod Rule)
To ensure the 4 team members can work simultaneously without merge conflicts or architectural inconsistencies:

### Pod A: Ingestion & Multimodal Extraction (Member A)
- **Directory**: `src/ingestion/`
- **Scope**: Document parsers (PDF, PPTX), Whisper video transcription + timestamp alignment, diagram captioning via Vision models.
- **Output**: Generates serialized `ContentUnit` records.
- **Rule**: Pod A does not touch the Graph, RAG, or Assessment engines.

### Pod B: Concept Graph, Retrieval & Grounding (Member B)
- **Directory**: `src/graph/`, `src/retrieval/`
- **Scope**: Concept & prerequisite extraction (NetworkX DAG), hybrid search (BM25 + Dense vector store), reranking, citation chip formatting, confidence-gated refusal logic.
- **Input**: Consumes `ContentUnit`.
- **Output**: Generates `ConceptNode` and grounded retrieved context.
- **Rule**: Pod B owns graph topology and retrieval interfaces.

### Pod C: Assessment & Learner Model (Member C)
- **Directory**: `src/assessment/`, `src/learner_model/`
- **Scope**: Quiz generation (MCQ, short answer, numerical), Dual-LLM verification + SymPy mathematical validation, deduplication, Bayesian Knowledge Tracing (BKT) engine, diagnostic test logic, prerequisite backward-walk.
- **Input**: Consumes `ConceptNode`.
- **Output**: Verified `Question` records and updated student mastery states.
- **Rule**: Pod C owns all BKT updates and assessment validation.

### Pod D: Frontend, Evaluation & Demo (Member D - Integration Lead)
- **Directory**: `src/ui/`, `src/eval/`, `src/api/`
- **Scope**: FastAPI service endpoints, UI dashboard (Streamlit / Next.js), RAGAS evaluation harness, simulated student ablation bench (Adaptive vs. Random), end-to-end integration.
- **Rule**: Pod D glues services together via the shared schemas without modifying internal pod logic directly.

---

### 3. Single Source of Truth: Shared Data Contracts
All inter-pod communication is strictly governed by `src/schemas/`:
1. `ContentUnit`: `{ unit_id, source_id, source_type, location, text, image_caption, embedding, topic_ids }`
2. `ConceptNode`: `{ concept_id, name, topic, prerequisites, evidence_units }`
3. `Question`: `{ q_id, topic, source_location, difficulty, type, stem, options, answer, verified, verifier_agreement, embedding }`
4. `LearnerState`: `{ student_id, concept_mastery, history, diagnostic_completed }`

No pod may modify shared schemas without explicit team consensus.
