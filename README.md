# Saarthi — A Verified Grounded Adaptive Tutor

Saarthi is an AI-powered learning system designed to transform scattered course material into a structured, source-aware knowledge base for personalized tutoring.

Instead of acting like a generic chatbot, Saarthi is being built to understand the student’s actual course material — including PDFs, lecture slides, diagrams, and eventually videos — while preserving exactly where every piece of information came from.

The larger goal is simple:

> Turn raw course material into a verified, multimodal knowledge system that can later power grounded tutoring, adaptive quizzes, and personalized learning.

---

## Current Development Status

This repository is currently focused on **Part 1: Multimodal Knowledge Base**.

The ingestion pipeline now supports:

- PDF upload and extraction
- Page-level source preservation
- Intelligent text chunking
- PDF image and figure extraction
- Groq-powered visual understanding
- PPT/PPTX text extraction
- Slide-level source preservation
- PPT image extraction
- Animated GIF conversion for vision processing
- Unified multimodal `ContentUnit` generation

The current pipeline can already convert both PDF and PowerPoint course material into structured text and visual units while preserving their original source location.

---

## What Saarthi Solves

Students rarely study from a single source.

A typical course may contain:

- Textbooks
- Lecture PDFs
- PowerPoint decks
- Diagrams
- Charts
- Screenshots
- Recorded lectures

Most basic RAG systems mainly extract text and ignore much of the visual information.

Saarthi takes a different approach.

It treats course material as **multimodal knowledge**.

That means:

- A diagram on Slide 7 is not lost.
- A graph on Page 14 is not ignored.
- A visual can be interpreted and converted into searchable academic information.
- Every extracted unit remembers exactly where it came from.

---

## Current Architecture

```text
                COURSE MATERIAL
                       |
           +-----------+-----------+
           |                       |
          PDF                     PPTX
           |                       |
           v                       v
     Text Extraction         Text Extraction
      via PyMuPDF            via python-pptx
           |                       |
           v                       v
        Chunking               Chunking
           |                       |
           +-----------+-----------+
                       |
                       v
               Structured Text Units

           PDF / PPT Visual Content
                       |
                       v
                Image Extraction
                       |
                       v
               Image Filtering
                       |
                       v
              Groq Vision Model
                       |
                       v
         Educational Visual Description
                       |
                       v
               Visual Content Units

                       |
                       v
              Unified Knowledge Units
```

---

## Core Idea — Content Units

Every piece of course material is normalized into a common structure called a `ContentUnit`.

### Example Text Unit

```json
{
  "unit_id": "machine_learning_p14_c2",
  "source_id": "machine_learning.pdf",
  "source_type": "pdf",
  "location": {
    "page": 14
  },
  "chunk_index": 2,
  "content_type": "text",
  "text": "Gradient descent is an optimization algorithm...",
  "visual_description": null,
  "image_path": null,
  "topic": null,
  "subtopic": null,
  "concept_ids": []
}
```

### Example Visual Unit

```json
{
  "unit_id": "ann_slides_s7_img1",
  "source_id": "ANN_slides.pptx",
  "source_type": "slides",
  "location": {
    "slide": 7
  },
  "chunk_index": null,
  "content_type": "visual",
  "text": "",
  "visual_description": "A neural network diagram showing an input layer, hidden layer, and output layer.",
  "image_path": "extracted_images/ann_slides_s7_img1.png",
  "topic": null,
  "subtopic": null,
  "concept_ids": []
}
```

This shared structure allows later components of Saarthi to work with PDFs and slides in the same way.

---

## Features Implemented So Far

### 1. PDF Ingestion

PDF files are processed using PyMuPDF.

For every page, Saarthi extracts:

- Text
- Page number
- Source filename
- Source type
- Structured content metadata

Pages without extractable text are preserved instead of being silently discarded, allowing OCR or vision processing to be added later.

---

### 2. Intelligent Text Chunking

Large pages are split into smaller retrieval-friendly chunks.

Each chunk preserves its original page number.

Example:

```text
Page 14
   |
   +-- Chunk 1
   +-- Chunk 2
   +-- Chunk 3
```

All three chunks still point back to:

```text
Page 14
```

This improves retrieval quality while preserving exact source information.

---

### 3. PDF Image & Diagram Extraction

Saarthi extracts embedded images from PDFs and filters out very small decorative images.

Useful visuals such as:

- Graphs
- Diagrams
- Charts
- Formulas
- Flowcharts
- Illustrations

are passed to a Groq vision-capable model.

The model converts the image into an academic description suitable for retrieval.

Example:

```text
Visual Input:
Gradient descent loss-surface diagram

Generated Description:
"A loss-surface diagram showing gradient descent iteratively moving toward the minimum."
```

Visuals without meaningful educational information can be ignored.

---

### 4. PowerPoint Ingestion

Saarthi also supports `.pptx` files.

For every slide, the system extracts:

- Slide text
- Slide number
- Embedded images
- Source metadata

Each slide is converted into structured text and visual units.

---

### 5. PowerPoint Visual Understanding

Images extracted from PowerPoint slides are passed through the same Groq-based visual understanding pipeline.

This allows Saarthi to understand content that ordinary text extraction could miss.

Examples include:

- Neural network diagrams
- Workflow diagrams
- Architecture figures
- Plots
- Confusion matrices
- Equations embedded as images

---

### 6. Animated GIF Handling

Some educational slide decks contain animated GIFs.

Vision APIs may reject animated GIFs directly, so Saarthi automatically converts them before processing:

```text
GIF
 |
 v
Extract first frame
 |
 v
Convert to PNG
 |
 v
Send to vision model
```

This prevents the ingestion pipeline from failing when an animated image appears inside a slide deck.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| PDF Processing | PyMuPDF |
| PowerPoint Processing | python-pptx |
| Vision Processing | Groq |
| Image Handling | Pillow |
| Data Validation | Pydantic |
| File Uploads | FastAPI UploadFile |
| Server | Uvicorn |
| Language | Python |

---

## Project Structure

```text
backend/
|
|-- app/
|   |
|   |-- api/
|   |   `-- knowledge.py
|   |
|   |-- ingestion/
|   |   |-- pdf_parser.py
|   |   |-- pdf_image_extractor.py
|   |   |-- pdf_pipeline.py
|   |   |-- ppt_parser.py
|   |   |-- ppt_image_extractor.py
|   |   `-- ppt_pipeline.py
|   |
|   |-- processing/
|   |   |-- chunker.py
|   |   |-- visual_processor.py
|   |   `-- ppt_visual_processor.py
|   |
|   |-- vision/
|   |   `-- image_captioner.py
|   |
|   |-- schemas/
|   |   `-- content_unit.py
|   |
|   `-- main.py
|
|-- uploads/
|
|-- extracted_images/
|
|-- requirements.txt
`-- .env
```

---

## API

### Upload Course Material

```http
POST /knowledge/upload
```

Currently supported formats:

```text
.pdf
.pptx
```

### Example PDF Response

```json
{
  "filename": "machine_learning.pdf",
  "source_type": "pdf",
  "status": "processed",
  "total_pages": 18,
  "total_slides": 0,
  "text_unit_count": 52,
  "visual_unit_count": 7,
  "content_unit_count": 59,
  "empty_units": 0
}
```

### Example PowerPoint Response

```json
{
  "filename": "ANN_Lecture.pptx",
  "source_type": "slides",
  "status": "processed",
  "total_pages": 0,
  "total_slides": 21,
  "text_unit_count": 34,
  "visual_unit_count": 9,
  "content_unit_count": 43
}
```

---

## Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/NansKong/Saarthi-A-Verified-Grounded-Adaptive-Tutor.git
```

### 2. Move into the backend

```bash
cd Saarthi-A-Verified-Grounded-Adaptive-Tutor/backend
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the environment on Windows

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Create a `.env` file

```env
GROQ_API_KEY=your_groq_api_key
```

### 7. Run the FastAPI server

```bash
uvicorn app.main:app --reload
```

### 8. Open Swagger UI

```text
http://127.0.0.1:8000/docs
```

---

## Development Roadmap

### Completed

```text
[✓] FastAPI backend setup
[✓] PDF ingestion
[✓] PDF page tracking
[✓] Text chunking
[✓] PDF image extraction
[✓] Groq visual captioning
[✓] PPTX text extraction
[✓] Slide-number preservation
[✓] PPTX image extraction
[✓] GIF-to-PNG fallback
[✓] Unified text + visual ContentUnits
```

### Next

```text
[ ] Lecture video ingestion
[ ] Groq Whisper transcription
[ ] Timestamp-preserving video chunks
[ ] Lecture keyframe extraction
[ ] Video visual understanding
[ ] Topic extraction
[ ] Subtopic extraction
[ ] Concept identification
[ ] Prerequisite graph generation
[ ] Embeddings
[ ] Vector database integration
```

---

## Where This Is Going

The Multimodal Knowledge Base is only the foundation.

Once ingestion is complete, Saarthi will use this structured content to build:

```text
Course Material
      |
      v
Multimodal Knowledge Base
      |
      v
Concept + Prerequisite Graph
      |
      v
Source-Grounded Retrieval
      |
      v
Verified Tutor
      |
      v
Adaptive Assessment
      |
      v
Learner Model
      |
      v
Personalized Learning Path
```

The goal is not to build another "chat with PDF" application.

The goal is to build a tutor that understands:

- what the course contains
- where the information came from
- what concepts depend on each other
- what the student already understands
- what the student should learn next

---

## Why Saarthi?

**Saarthi** means a guide — someone who helps navigate the path ahead.

That idea fits the project perfectly.

The system is not supposed to replace course material.

It is supposed to guide the student through it.

---

## Current Milestone

The current milestone successfully demonstrates:

> **PDF + PPTX → text + visuals → source-aware structured knowledge units**

The next phase will extend the same pipeline to lecture videos, topic and concept extraction, prerequisite modelling, embeddings, and vector-based retrieval.

---

## Contributors

Built as part of the **Multimodal AI Hackathon 2026 — Track D: Personalized Tutoring & Adaptive Learning**.
