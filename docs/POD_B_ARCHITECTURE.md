# Saarthi - Pod B: concept graph, retrieval and grounding

Pod B turns the Content Units produced by Pod A into a knowledge layer the rest of the product can trust:
what the course covers, how its concepts depend on each other, and answers that are tied to exact places in the
material - or an honest refusal.

## 1. Architecture

```
 Pod A units (page / slide / video timestamp)            Pod C: quizzes           Pod D: UI + evaluation
        |  POST /pod-b/ingest/units  (or POD_B_CORPUS)         ^  /concepts/{id}/units    ^  /ask  /graph  /search
        v                                                      |                          |
 +-----------+   +-----------------+   +------------------+   |   +---------------------------------------+
 | CorpusStore|-->| HybridRetriever |-->| GroundedAnswerer |---+-->|  FastAPI  /pod-b/*  (+ /sources/{id}) |
 +-----------+   | BM25 + embeddings|   | gate -> LLM ->   |       +---------------------------------------+
        |        | -> RRF -> rerank |   | claim check      |
        v        +--------^---------+   +---------^--------+
 +----------------+       | evidence boost        | concept match, topics
 | KnowledgeGraph |-------+-----------------------+
 | topics>concepts|  built by GraphBuilder (Gemini) -> validate edges -> enforce DAG -> tag units
 +----------------+
```
State lives in one immutable `Bundle` swapped atomically under a lock, so ingest and graph rebuilds never expose a
half-built index to a request.

## 2. Data contracts (additions to the team's frozen schemas are non-breaking)
- **ContentUnit** - as frozen; Pod B back-fills `topic_ids` (concept's topic plus ancestors) and `concept_ids`.
  Pod A's `embedding` is ignored: queries and documents must be embedded by the same model.
- **ConceptNode** - `prerequisites` stays `list[str]` for Pod C and contains **validated edges only**. Added:
  `definition`, `aliases`, `prerequisite_edges` (confidence, validated, signals, evidence units, proposer confidence).
- **AnswerResponse** - `status` (grounded | partial | refused), `answer` with `[n]` markers, numbered `sources`
  (label, excerpt, deep link `/sources/{id}#page=|#slide=|?t=`), `claims`, `outside_knowledge`, `retrieved` unit ids.

## 3. Retrieval
BM25 and dense embeddings rank independently; reciprocal-rank fusion merges them; a reranker scores the top 20.
The reranker score (0-1) is reported as `relevance` and is what the refusal gate reads. If the question names a known
concept, that concept's evidence units get a +0.2 ordering boost (added to the candidate pool if needed), so a
definition outranks a passing mention. Backends are chosen by environment: hosted embeddings when a key is present,
else local sentence-transformers + cross-encoder, else a dependency-free hashing/lexical fallback. Document
embeddings are cached on disk, so a paid API embeds each unit once.

## 4. Knowledge graph
1. **Extract** (LLM, per batch of units): concepts with definition, aliases and the unit ids that explain them.
   Unit ids the model invents are dropped; a concept left with no real evidence is dropped.
2. **Merge** duplicates across batches by normalised name/alias.
3. **Organise** (one LLM call): topic/subtopic tree, assignments, proposed prerequisites with confidence.
4. **Validate** each prerequisite against the material. An edge "A requires P" is accepted only if
   (a) a unit explaining A mentions P by name/alias, or (b) P is introduced earlier than A in a shared source and the
   proposer was >= 0.8 confident. Edges the material contradicts are rejected. The LLM proposes; the text decides.
5. **Enforce a DAG** by dropping the weakest edge of each cycle, then **tag** every unit: by evidence first, then by
   BM25 against concept descriptions for the rest.

## 5. Grounding method
1. **Retrieval gate** - refuse before spending an LLM call if top relevance is below a per-backend threshold and the
   question names no known concept. Two thresholds exist because failures differ: *strict* (best balanced accuracy)
   when nothing downstream can catch a bad pass, *permissive* (0.8 x lowest in-scope score) when an LLM judge follows.
2. **LLM judgement** - answer only from numbered excerpts as atomic claims, each citing unit ids; or declare the
   material does not cover it.
3. **Claim check** - cited ids must be retrieved units; each claim's content words must be mostly present in its
   cited units; optionally (`VERIFY_WITH_LLM=1`) an LLM fact-checks each claim. Failing claims are never shown as
   source-backed: they move to `outside_knowledge` and the status becomes *partial*. No supported claim -> *refused*.
4. **Near-miss flag** - a term the course never uses placed next to a concept it does cover ("convolutional neural
   network", "derivative of sin x") caps the status at *partial* with an explanation, and tells the LLM.
5. **Outside knowledge** is returned only when the caller opts in, only for refused questions, and always labelled.
6. **Degradation** - no LLM (or an LLM failure) falls back to extractive mode: verbatim excerpts under the strict gate.

## 6. Evaluation (Pod B's own smoke metrics; Pod D owns the RAGAS/DeepEval run via `/ask`)
`python scripts/eval_grounding.py` on the bundled 28-unit corpus, 20 in-scope / 10 off-topic / 4 near-miss queries,
**fallback backend, no LLM** (`eval_results/grounding_dev_eval.json`):

| Metric | Result |
|---|---|
| Correct unit ranked first / in top 3 | 95% / 100% |
| Cited units that were correct (citation precision) | 82% |
| Answers containing at least one correct citation | 100% |
| In-scope questions answered | 19 / 20 |
| Off-topic questions refused | 10 / 10 |
| Near-miss questions not confidently grounded | 4 / 4 (2 refused by the gate, 2 flagged partial) |
| Graph: validated edges / hand-labelled edges | 17 / 17 (extractor vs gold not yet measured: needs the Gemini key) |

**Read these honestly.** One author wrote the corpus, the graph and the queries, so every number is optimistic and
only a regression baseline. The corpus is 28 units. The fallback has no semantics, so paraphrase handling is its
weak spot (the one in-scope miss). The near-miss detector's verb list was tuned after seeing two false positives.
Generative-mode quality, extractor-vs-gold graph accuracy and real-embedding retrieval have **not** been measured here.

## 7. API (all under `/pod-b`)
| Endpoint | Purpose |
|---|---|
| `POST /ask` | grounded answer (rate-limited) |
| `GET /search`, `/units`, `/units/{id}` | retrieval and raw units |
| `GET /graph`, `/topics`, `/concepts`, `/concepts/{id}`, `/concepts/{id}/units`, `/coverage` | graph and tagging |
| `POST /ingest/units` | add or replace units live (admin token if set) |
| `POST /graph/rebuild`, `GET /graph/status` | background LLM graph rebuild (admin token if set) |
| `GET /health`, `/retrieval/info`, `/ask/info` | what is running and why |
| `GET /sources/{source_id}` | original file, if `POD_B_SOURCES_DIR` is set |

## 8. Configuration (env or `.env`; see `.env.example`)
`GEMINI_API_KEY` (or `OPENAI_API_KEY` for embeddings), `EMBEDDING_PROVIDER`, `RERANK_PROVIDER`, `LLM_MODEL`,
`VERIFY_WITH_LLM`, `POD_B_ADMIN_TOKEN`, `POD_B_RATE_LIMIT`, `POD_B_CORS_ORIGINS`, `POD_B_SOURCES_DIR`,
`POD_B_CORPUS`, `POD_B_GRAPH`, `POD_B_CACHE_DIR`.

## 9. Known limitations
- Gemini and OpenAI code paths are verified against recorded/fake responses only; run `scripts/check_gemini.py` first.
- Refusal thresholds are calibrated on 30 queries and must be re-calibrated per backend and per course.
- The graph is rebuilt in full (no incremental update); new units are searchable and tagged immediately but create no
  new concepts until a rebuild.
- Prerequisite validation relies on the extractor supplying good aliases, and its order signal needs a shared source.
- The claim check is lexical (plus optional LLM); a fluent but subtly wrong claim that reuses the cited words can pass.
- Rate limiting and the admin token are single-process protections for a demo server, not a full auth system.

## 10. Integration checklist
- **Pod A:** units must satisfy `ContentUnit` (anchor type matches `source_type`); you may omit embeddings and tags.
- **Pod C:** read `/concepts/{id}/units` for question sources; `prerequisites` are validated edges only; `student_context`
  on `/ask` is the hook for mastery-aware explanations.
- **Pod D:** render `sources` as chips linking `open_url`; show `outside_knowledge` visibly distinct; run RAGAS on
  `question`, `answer`, `retrieved`; set `POD_B_CORS_ORIGINS` to your dev origin.
