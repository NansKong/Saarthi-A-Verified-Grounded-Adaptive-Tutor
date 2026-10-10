# Saarthi — A Verified-Grounded Adaptive Tutor

Saarthi is an AI-powered adaptive tutoring system designed to learn directly from course material and build a grounded, structured knowledge base before generating educational responses.

Instead of relying only on a general-purpose LLM, Saarthi ingests actual learning resources such as textbooks, lecture slides, and videos, extracts their concepts, organizes relationships between them, and preserves source-level evidence such as page numbers, slide numbers, and timestamps.

The long-term goal is to create a tutor that can answer, explain, revise, and adapt to a learner while remaining grounded in verified course content.

---

## Current Development Stage

### Part 1 — Multimodal Knowledge Base

The current implementation focuses on building the knowledge layer behind Saarthi.

It supports:

- PDF textbooks and notes
- PowerPoint presentations
- Lecture videos
- Text extraction
- Image and diagram understanding
- Video transcription
- Keyframe extraction
- Semantic concept extraction
- Concept normalization and deduplication
- Prerequisite relationship generation
- Embedding generation
- Vector search
- Persistent knowledge storage
- Source-grounded retrieval
- Provider fallback
- Checkpoint-based recovery

---

# Why Saarthi?

Most AI tutors can produce explanations, but they do not necessarily know:

- what material the student has actually studied
- what concepts are part of a particular course
- which concepts depend on others
- where a concept appeared in the source material
- whether an answer is grounded in the provided resources

Saarthi addresses this by first transforming educational material into a structured multimodal knowledge base.

The tutor layer can later use this knowledge base to generate explanations that are both personalized and traceable to the original course material.

---

# System Architecture

```text
                PDF / PPTX / MP4
                       │
                       ▼
             Multimodal Ingestion
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
   Text Extraction              Visual Extraction
        │                             │
        │                    Images / Keyframes
        │                             │
        │                             ▼
        │                     Vision Understanding
        │                             │
        └──────────────┬──────────────┘
                       │
                       ▼
                 ContentUnits
                       │
                       ▼
              Semantic Extraction
                       │
                       ▼
             Concept Normalization
                       │
                       ▼
                Concept Registry
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼                       ▼
      Embeddings             Prerequisite Graph
           │                       │
           ▼                       ▼
         Qdrant              Knowledge Graph
           │                       │
           └───────────┬───────────┘
                       │
                       ▼
               Grounded Retrieval
                       │
                       ▼
             Adaptive Tutor Layer
                 (Next Phase)
```

---

# Core Features

## 1. Multimodal Document Ingestion

Saarthi accepts multiple educational content formats without requiring manual preprocessing.

### Supported Formats

| Format | Processing |
|---|---|
| PDF | Text extraction, page-level grounding, embedded image extraction |
| PPTX | Slide text extraction, image extraction, slide-level grounding |
| MP4 | Audio extraction, transcription, keyframe extraction, timestamp grounding |

---

# 2. ContentUnit Representation

Every extracted piece of knowledge is converted into a common `ContentUnit` representation.

A ContentUnit may contain:

```python
{
    "unit_id": "...",
    "source_id": "...",
    "source_type": "pdf | slides | video",

    "location": {
        "page": 5
    },

    "content_type": "text | visual",

    "text": "...",

    "visual_description": "...",

    "image_path": "...",

    "topic": "...",

    "subtopic": "...",

    "concept_ids": [...]
}
```

This allows Saarthi to process PDFs, slides, and videos through the same downstream semantic pipeline.

---

# 3. Source-Level Grounding

Every ContentUnit preserves its original source location.

### PDF

```json
{
    "page": 12
}
```

### Presentation

```json
{
    "slide": 7
}
```

### Video

```json
{
    "timestamp": {
        "start": 1973.9,
        "end": 1973.9
    }
}
```

This allows future tutor responses to reference the material from which an explanation was derived.

For example:

```text
According to Lecture 1 at approximately 32:53...
```

or:

```text
This concept is discussed on page 12 of the uploaded textbook.
```

---

# 4. PDF Processing

The PDF ingestion pipeline uses PyMuPDF for document parsing.

It performs:

```text
PDF
 │
 ├── Extract page text
 │
 ├── Split text into semantic chunks
 │
 ├── Preserve page metadata
 │
 ├── Extract embedded images
 │
 ├── Analyze educational visuals
 │
 └── Generate ContentUnits
```

Text chunks remain linked to their original page.

Embedded figures and diagrams can also become visual ContentUnits.

---

# 5. PowerPoint Processing

Presentations are processed using `python-pptx`.

The pipeline extracts:

- slide text
- slide images
- slide numbers
- visual descriptions

Animated GIF images are converted to a usable static frame before analysis when required.

Each extracted unit remains grounded to its slide.

---

# 6. Video Processing

Videos are processed through both audio and visual pipelines.

```text
Video
 │
 ├── FFmpeg audio extraction
 │
 ├── Whisper transcription
 │
 ├── Timestamped transcript chunks
 │
 ├── Full-duration keyframe extraction
 │
 ├── Educational visual detection
 │
 ├── Vision-language analysis
 │
 └── Multimodal ContentUnits
```

---

## Audio Processing

FFmpeg extracts optimized audio from lecture videos.

The audio is sent to Groq Whisper using:

```text
whisper-large-v3-turbo
```

Transcript segments are merged into approximately 45-second ContentUnits.

Each transcript unit preserves start and end timestamps.

---

## Keyframe Extraction

Rather than sampling only the beginning of long videos, Saarthi divides the entire video duration into temporal regions.

Multiple candidate frames are examined within each region and a representative frame is selected using visual difference.

Example:

```text
68-minute lecture
      │
      ▼
12 temporal regions
      │
      ▼
candidate frames per region
      │
      ▼
visual-difference scoring
      │
      ▼
representative keyframe
```

This ensures visual coverage across the complete lecture.

---

# 7. Educational Vision Understanding

Extracted images and video keyframes are analyzed using a multimodal LLM.

The system focuses on academically meaningful information such as:

- diagrams
- graphs
- charts
- equations
- formulas
- workflows
- tables
- labelled structures
- technical illustrations
- instructional text
- relationships between concepts

Non-educational elements such as logos, decorative backgrounds, classroom furniture, and branding are ignored.

Frames without meaningful academic information can be classified as:

```text
NOT_EDUCATIONAL
```

and excluded from the knowledge base.

---

# 8. Semantic Extraction

ContentUnits are enriched with structured semantic information.

The semantic layer identifies:

```text
Topic
Subtopic
Concepts
```

Example:

```json
{
    "topic": "Machine Learning",
    "subtopic": "Supervised Learning",
    "concepts": [
        "Training Data",
        "Classification",
        "Regression"
    ]
}
```

---

# 9. Batched Semantic Processing

Semantic extraction is performed in batches instead of making one LLM request per ContentUnit.

Example:

```text
5 ContentUnits
      │
      ▼
1 Semantic Extraction Request
      │
      ▼
Concept Normalization
```

This significantly reduces:

- API requests
- processing time
- rate-limit pressure
- LLM cost

---

# 10. Concept Normalization and Deduplication

Different educational resources often describe the same concept differently.

Examples:

```text
Neural Network
Neural Networks

Prediction
Predictions

Gradient Descent
Gradient Descent Algorithm
```

Saarthi attempts to map these variations to the same canonical concept.

Normalization follows multiple stages:

```text
Incoming Concept
      │
      ▼
Exact Match
      │
      ▼
Alias Match
      │
      ▼
Lexical Normalization
      │
      ▼
Qdrant Semantic Candidates
      │
      ▼
Batched LLM Verification
```

This prevents the concept graph from becoming unnecessarily fragmented.

---

# 11. Concept Registry

Concepts are maintained in a centralized registry.

Each concept stores:

```python
{
    "concept_id": "...",
    "name": "...",
    "aliases": [...],
    "topic": "...",
    "subtopic": "...",
    "evidence_units": [...],
    "prerequisites": [...]
}
```

`evidence_units` connect concepts back to the original ContentUnits that introduced or explained them.

---

# 12. Prerequisite Knowledge Graph

Saarthi builds prerequisite relationships between concepts.

Example:

```text
Training Data
      │
      ▼
Model Training
      │
      ▼
Model Evaluation
      │
      ▼
Model Deployment
```

or:

```text
Decision Trees
      │
      ▼
Random Forests
```

Potential prerequisite candidates are retrieved using semantic similarity and verified through an LLM.

Prerequisite processing is batched to reduce API usage.

---

# 13. Graph Safety

The Concept Registry validates prerequisite relationships before adding them.

It prevents:

- self-referencing prerequisites
- duplicate edges
- invalid concept references
- cyclic dependencies

Example of an invalid graph:

```text
A → B → C → A
```

Saarthi detects and prevents such cycles.

---

# 14. Embeddings

Saarthi currently uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Embedding dimension:

```text
384
```

Embeddings are generated for both:

- ContentUnits
- Concepts

These vectors enable semantic retrieval across the knowledge base.

---

# 15. Vector Database

Saarthi currently uses Qdrant as its vector database.

Collections:

```text
saarthi_content
saarthi_concepts
```

### Content collection

Stores:

- text
- visual descriptions
- embeddings
- source information
- page/slide/timestamp metadata
- topic
- subtopic
- concept IDs

### Concept collection

Stores:

- concept names
- aliases
- topic
- subtopic
- evidence units
- prerequisite relationships
- embeddings

---

# 16. Persistent Concept Registry

The in-memory Concept Registry is reconstructed from Qdrant whenever the FastAPI application starts.

Startup flow:

```text
FastAPI Starts
      │
      ▼
Qdrant Loaded
      │
      ▼
Restore Concept Nodes
      │
      ▼
Restore Prerequisite Edges
      │
      ▼
Validate Graph
      │
      ▼
Knowledge Base Ready
```

Concept restoration happens in two passes.

### Pass 1

Restore every concept node.

### Pass 2

Restore prerequisite relationships.

This ensures prerequisite concepts exist before graph edges are recreated.

---

# 17. Checkpoint-Based Recovery

Long processing tasks should not have to restart completely when an API provider becomes unavailable.

Saarthi stores checkpoints for completed semantic and prerequisite work.

Example:

```text
checkpoints/
│
├── semantic/
│
└── prerequisites/
```

If processing stops midway:

```text
Batch 1 ✅
Batch 2 ✅
Batch 3 ❌ Provider unavailable
```

the next run can restore completed batches and continue from the unfinished section.

---

# 18. LLM Provider Fallback

Saarthi currently uses a provider fallback architecture.

```text
Groq
 │
 │ failure / rate limit
 ▼
Gemini
 │
 │ unavailable
 ▼
Deferred Processing
```

Groq is used as the primary provider.

Gemini is used as a fallback when Groq becomes unavailable or rate-limited.

The same architecture is used for both semantic processing and multimodal visual analysis.

---

# 19. Graceful Quota Handling

LLM API quotas should not cause an uploaded course resource to disappear.

If all configured providers become unavailable:

```text
Content extraction       ✅
Embeddings               ✅
Completed checkpoints    ✅
Qdrant persistence       ✅

Remaining semantic work  ⏸ Deferred
Graph generation         ⏸ Deferred
```

The API can still return a successful response with a status such as:

```json
{
    "semantic_status": "deferred_llm_unavailable",
    "graph_status": "deferred_semantic_processing"
}
```

This allows processing to resume later rather than failing the entire ingestion request.

---

# API

The backend is built using FastAPI.

Start the server with:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

for Swagger documentation.

---

## Root

```http
GET /
```

Example:

```json
{
    "message": "Saarthi Multimodal Knowledge Base API is running.",
    "concepts_loaded": 337
}
```

---

## Upload Educational Material

```http
POST /knowledge/upload
```

Supported uploads:

```text
.pdf
.pptx
.mp4
```

Example response:

```json
{
    "filename": "machine_learning.pdf",
    "source_type": "pdf",

    "content_unit_count": 25,

    "affected_concept_count": 18,

    "concept_count": 120,

    "edge_count": 34,

    "has_cycles": false,

    "semantic_status": "completed",

    "graph_status": "completed"
}
```

---

## Concepts

```http
GET /concepts/
```

Returns the current concept registry.

---

## Concept Graph

```http
GET /graph/concept/{concept_id}
```

Example:

```http
GET /graph/concept/decision_trees
```

This can be used to inspect prerequisite relationships for a concept.

---

## Semantic Search

```http
GET /search/?q={query}&limit={limit}
```

Example:

```http
GET /search/?q=neural%20networks&limit=5
```

The search layer performs semantic retrieval over grounded ContentUnits.

---

# Project Structure

```text
backend/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   ├── knowledge.py
│   │   ├── concepts.py
│   │   ├── graph.py
│   │   └── search.py
│   │
│   ├── schemas/
│   │   └── content_unit.py
│   │
│   ├── ingestion/
│   │   ├── pdf_parser.py
│   │   ├── pdf_image_extractor.py
│   │   ├── pdf_pipeline.py
│   │   ├── ppt_parser.py
│   │   ├── ppt_image_extractor.py
│   │   ├── ppt_pipeline.py
│   │   ├── audio_extractor.py
│   │   ├── video_transcriber.py
│   │   ├── keyframe_extractor.py
│   │   └── video_pipeline.py
│   │
│   ├── processing/
│   │   ├── chunker.py
│   │   ├── transcript_chunker.py
│   │   ├── semantic_processor.py
│   │   ├── batch_semantic_extractor.py
│   │   ├── concept_extractor.py
│   │   ├── concept_normalizer.py
│   │   ├── batch_concept_normalizer.py
│   │   ├── concept_registry_processor.py
│   │   ├── embedding_processor.py
│   │   ├── concept_embedding_processor.py
│   │   ├── batch_prerequisite_extractor.py
│   │   └── knowledge_graph_builder.py
│   │
│   ├── knowledge/
│   │   ├── concept_registry.py
│   │   ├── course_registry.py
│   │   ├── registry_persistence.py
│   │   ├── graph_validator.py
│   │   ├── graph_queries.py
│   │   └── knowledge_base_builder.py
│   │
│   ├── embeddings/
│   │   └── embedding_service.py
│   │
│   ├── vectorstore/
│   │   ├── qdrant_service.py
│   │   ├── content_store.py
│   │   ├── content_search.py
│   │   ├── concept_store.py
│   │   └── concept_search.py
│   │
│   ├── vision/
│   │   └── image_captioner.py
│   │
│   ├── llm/
│   │   └── text_llm.py
│   │
│   └── checkpoints/
│       └── checkpoint_service.py
│
├── checkpoints/
├── uploads/
├── extracted_audio/
├── extracted_images/
├── extracted_keyframes/
├── qdrant_data/
│
├── .env
├── requirements.txt
└── README.md
```

Runtime folders are intentionally excluded from Git.

---

# Setup

## 1. Clone the repository

```bash
git clone <repository-url>
cd Saarthi-A-Verified-Grounded-Adaptive-Tutor/backend
```

---

## 2. Create a Virtual Environment

### Windows

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# FFmpeg

FFmpeg is required for video audio extraction.

Verify installation using:

```bash
ffmpeg -version
```

If the command is not recognized, install FFmpeg and add it to your system PATH.

---

# Environment Variables

Create:

```text
backend/.env
```

Do not commit this file.

Example:

```env
GROQ_API_KEY=
model=qwen/qwen3.8-27b

GEMINI_API_KEY=
GEMINI_TEXT_MODEL=gemini-3.8-flash
GEMINI_VISION_MODEL=gemini-3.8-flash

GEMINI_MIN_INTERVAL_SECONDS=13
GEMINI_MAX_RETRY_WAIT_SECONDS=15

HF_TOKEN=
```

`HF_TOKEN` is optional but may provide improved Hugging Face download limits.

Never place production API keys directly inside source files or commit `.env` files.

---

# Running Saarthi

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

Expected startup flow:

```text
[Qdrant] Collection exists: saarthi_content
[Qdrant] Collection exists: saarthi_concepts

[Saarthi Startup] Initializing knowledge base...

[Registry Restore] Loading concepts from Qdrant...
[Registry Restore] ... concept(s) restored.
[Registry Restore] ... prerequisite edge(s) restored.
[Registry Restore] Graph valid: True

[Saarthi Startup] Knowledge base ready.

Application startup complete.
```

---

# Example Knowledge Flow

Suppose a machine-learning lecture introduces:

```text
Supervised Learning
Training Data
Model Training
Model Evaluation
Random Forest
```

Saarthi may construct:

```text
Training Data
     │
     ▼
Supervised Learning
     │
     ▼
Model Training
     │
     ▼
Model Evaluation
```

and:

```text
Decision Trees
     │
     ▼
Random Forest
```

Each node remains connected to the PDF page, PowerPoint slide, or lecture timestamp where the concept was observed.

---

# Current Status

## Multimodal Ingestion

- [x] PDF ingestion
- [x] PPTX ingestion
- [x] MP4 ingestion
- [x] PDF image extraction
- [x] PPT image extraction
- [x] Video transcription
- [x] Video keyframe extraction
- [x] Vision-based educational image understanding

## Semantic Processing

- [x] Topic extraction
- [x] Subtopic extraction
- [x] Concept extraction
- [x] Batched semantic extraction
- [x] Concept normalization
- [x] Lexical deduplication
- [x] Embedding-based candidate retrieval
- [x] Batched semantic concept verification

## Knowledge Graph

- [x] Concept Registry
- [x] Evidence linking
- [x] Prerequisite generation
- [x] Batched prerequisite extraction
- [x] Cycle prevention
- [x] Graph validation
- [x] Graph persistence

## Persistence

- [x] ContentUnit storage in Qdrant
- [x] Concept storage in Qdrant
- [x] Deterministic concept IDs
- [x] Persistent Qdrant collections
- [x] Registry reconstruction on startup
- [x] Prerequisite restoration

## Reliability

- [x] Semantic checkpoints
- [x] Prerequisite checkpoints
- [x] Groq → Gemini fallback
- [x] Gemini rate-limit handling
- [x] Deferred processing during provider failure
- [x] Partial ingestion persistence
- [x] HTTP success despite recoverable LLM exhaustion

## Retrieval

- [x] Content semantic search
- [x] Concept semantic search
- [x] Page-level provenance
- [x] Slide-level provenance
- [x] Timestamp-level provenance

---

# Current Limitations

The current Part 1 implementation is functional but still has several areas planned for hardening.

## Vision Cache

Video keyframes may currently be analyzed again during repeated ingestion runs.

A content-hash-based vision cache is planned to avoid repeated multimodal API calls.

## Duplicate Video Frames

Short videos can produce visually similar keyframes.

A near-duplicate threshold can be added to avoid unnecessary vision requests.

## Checkpoint Versioning

Semantic checkpoints currently depend primarily on ContentUnit identity.

Content hashing is planned so a checkpoint is invalidated automatically when underlying content changes.

## Testing

Some older development scripts were written as live integration checks rather than isolated pytest unit tests.

The test architecture is being separated into:

```text
tests/
├── unit/
└── integration/
```

Unit tests will avoid live LLM and persistent vector database dependencies.

---

# Planned Improvements

## Part 1 Hardening

- [ ] Vision description caching
- [ ] Near-duplicate keyframe filtering
- [ ] Content-hash checkpoint validation
- [ ] Source-level ingestion registry
- [ ] Duplicate file detection
- [ ] Source deletion / replacement
- [ ] Knowledge-base consistency audit
- [ ] Concept fragmentation audit
- [ ] Dedicated unit and integration test suites

---

# Future Roadmap

## Part 2 — Grounded Tutoring

Use the knowledge base to answer questions using only relevant educational evidence.

Planned capabilities:

- grounded question answering
- evidence citation
- retrieval-augmented explanations
- source-aware tutoring

---

## Part 3 — Adaptive Learning

Introduce learner-specific modeling.

Potential features:

- concept mastery tracking
- knowledge gaps
- prerequisite gap detection
- personalized revision recommendations
- difficulty adaptation
- explanation-style adaptation

---

## Part 4 — Assessment Engine

Generate assessments grounded in uploaded course material.

Potential features:

- MCQs
- descriptive questions
- concept-specific quizzes
- difficulty-controlled questions
- misconception detection
- adaptive testing

---

## Part 5 — Personalized Learning Path

The final tutor can use:

```text
Course Knowledge Graph
        +
Learner Mastery Graph
        +
Prerequisite Relationships
        +
Retrieval Evidence
        │
        ▼
Personalized Learning Path
```

This allows Saarthi to decide not only **what to explain**, but also **what the learner should study next and why**.

---

# Design Principles

Saarthi is being built around five core principles.

## Grounded

Responses should originate from actual educational material whenever possible.

## Traceable

Knowledge should retain evidence pointing back to pages, slides, timestamps, and visuals.

## Multimodal

Educational understanding should not be limited to extracted text.

## Recoverable

External LLM failures should not destroy completed processing work.

## Adaptive

The final system should adapt the learning experience to the learner rather than providing identical tutoring to everyone.

---

# Security

The following files and directories must never be committed:

```text
.env
venv/
uploads/
qdrant_data/
checkpoints/
extracted_audio/
extracted_images/
extracted_keyframes/
__pycache__/
```

API credentials should always be loaded through environment variables.

If an API key is ever accidentally committed, it should be revoked and replaced immediately.

---

# Git Ignore Recommendations

```gitignore
backend/.env
backend/venv/

backend/uploads/
backend/extracted_audio/
backend/extracted_images/
backend/extracted_keyframes/

backend/qdrant_data/
backend/checkpoints/

**/__pycache__/
*.pyc

.pytest_cache/
```

---

# Tech Stack

## Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

## Document Processing

- PyMuPDF
- python-pptx
- Pillow

## Video / Audio

- FFmpeg
- OpenCV
- Groq Whisper

## AI / LLM

- Groq
- Gemini
- Sentence Transformers

## Embeddings

- `sentence-transformers/all-MiniLM-L6-v2`

## Vector Database

- Qdrant

## Storage / Recovery

- Qdrant persistent local storage
- JSON checkpoints

---

# Project Goal

The objective of Saarthi is not simply to build another chatbot.

The goal is to build an educational intelligence system that understands:

```text
What is being taught?
        │
What concepts exist?
        │
How are they connected?
        │
Where did the information come from?
        │
What does the learner understand?
        │
What should they learn next?
```

Part 1 establishes the foundation required to answer the first four questions.

The adaptive tutor layer will build on this knowledge base to address the final two.

---

## Saarthi

**Learn from the course. Understand the learner. Teach with evidence.**
