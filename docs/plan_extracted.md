Multimodal AI Hackathon 2026  ·  Track D
Saarthi — A Verified-Grounded Adaptive Tutor
Team plan: the problem, our idea in plain language, how we divide the work, and the tools we use.
This document has four parts. Part 1 restates the problem statement in plain language. Part 2 explains our idea in simple terms, so any team member can follow it without a machine-learning background. Part 3 splits the work across our four members. Part 4 lists the tools and stack.
Part 1 — The Problem Statement, in Plain Words
1.1  What the track is asking for
Track D is called “Personalized Tutoring & Adaptive Learning.” It asks for one thing: build an AI study companion that (a) pulls lecture videos, textbooks and slide decks into a single searchable knowledge base, (b) always answers with a citation pointing back to the exact place the answer came from, and (c) uses that knowledge to quiz the student and adapt to what they already know. It is not a general chatbot — it is a tutor that stays tied to the course material.
1.2  Why this is a real problem
Students study from material scattered everywhere — a lecture video here, a textbook PDF there, a slide deck somewhere else. General chatbots will happily answer, but their answers are not tied to the course, are not tied to what this particular student has already understood, and can be confidently wrong. A companion grounded in the actual course, that also models the learner, makes study time both more trustworthy and more effective.
1.3  The six requirement groups, one line each
Requirement
What it means in practice
1. Multimodal Knowledge Base
Ingest videos, textbooks and slides with no manual preprocessing. Organise them into topics, concepts and prerequisites. Link every unit to its origin (page, slide number, or video timestamp). Actually use the images, diagrams and figures, not just the text.
2. Source Grounding
Answer and explain using cited excerpts that open the exact page, slide or timestamp. Decline — or clearly flag — anything the material does not cover, keeping outside knowledge visibly separate from source-backed content.
3. Adaptive Assessment
Generate quizzes and mock exams (MCQ, short answer, numerical) on a student-chosen scope, each question tagged with topic, source location and difficulty. Verify question correctness and avoid repeating questions. Give cited feedback and a post-assessment report of weak topics and likely misconceptions.
4. Learner Model
Keep a per-topic mastery estimate that updates after every quiz and conversation (Bayesian knowledge tracing, IRT, or spaced repetition). Handle brand-new students with no history via a short diagnostic.
5. System Evaluation
Evaluate the pipeline with a standard framework (RAGAS, DeepEval, TruLens). Report faithfulness, answer relevancy and context precision/recall on a team-built test set. Measure personalization with simulated student profiles across multiple sessions.
6. Optional Enhancements
Visual course flow map; weak-topic revision material (flashcards, slides, audio briefs); a study schedule using forgetting curves; Indian-language interaction (English lectures with Hindi explanations); audio-based tutoring.
1.4  What we must hand in
Working software prototype (web/app): the ingestion workflow, source-grounded tutor chat, adaptive assessment generator, and a dashboard.
Project documentation: architecture, grounding method, learner-model approach.
Evaluation & benchmarking: framework metrics plus simulated-student results on our chosen course material.
A 3–10 minute demo video showing the working system end to end.
1.5  How we are scored
Evaluation criterion
Weight
Knowledge Base & Grounding — extraction accuracy, source links, citation accuracy, correct refusal of unsupported queries
20%
Assessment Quality — question correctness and novelty, topic/source tagging, usefulness of feedback and reports
15%
Personalization Effectiveness — learner-model approach, measurable gains in simulated runs, responsiveness to student state
20%
User Experience & Demo Video — dashboard clarity, UI/UX workflow, usability, optional features
15%
System Evaluation — choice of framework and metrics, test-set quality, rigor and honesty of results
15%
Technical Implementation — code quality and system architecture
15%
The first three criteria — grounding, assessment and personalization — add up to 55% of the score, and they are exactly where most teams are weakest. That is where our design concentrates its effort.
Part 2 — Our Idea, Explained Simply
2.1  The key idea
The AI should not just answer questions. It should know what the student has learned, what they need to learn next, and exactly where every answer came from.
2.2  Why a normal AI tutor is not enough
Imagine a student uploads their lecture PDFs, PPT slides and lecture videos. A normal AI tutor would simply answer whatever is asked. But that leaves big questions open:
Is that information actually in the student's lecture, or is the AI making it up?
Which slide explains it — where did this answer come from?
Does the student already understand the prerequisites (for example, derivatives before gradient descent)?
Should the next question be about gradient descent, or about the prerequisite the student is weak in?
Is the quiz question itself even correct?
Our system tries to solve all of these at once. That is what makes it a tutor, not a chatbot.
2.3  The project in one sentence
Build an AI tutor that understands the student's course material, builds a map of concepts and prerequisites, teaches only from verified material, generates verified questions, and adapts to the student's weaknesses.
That is the whole project. Everything else in this document supports it.
2.4  The most important part: the concept graph
This is the heart of the system. Suppose the uploaded lecture contains a chain of ideas. The system builds a knowledge graph out of them, and draws prerequisite links between concepts:
Derivatives
     |  prerequisite
     v
Chain Rule
     |  prerequisite
     v
Gradient Descent
     |  prerequisite
     v
Neural Networks
Each concept also remembers where it came from — its evidence:
Gradient Descent
    |-- Slide:     14
    |-- Lecture:   02
    |-- Timestamp: 12:41
    |-- Source:    ML_Lecture_2.pdf
So the AI does not just know that “gradient descent exists.” It knows that “gradient descent is explained on Slide 14.” That is why we call the system grounded — every claim is tied back to a real place in the student's own material.
2.5  Why prerequisites are important
This is where the project becomes smarter than a basic chatbot. Suppose a student asks: “Why isn't my neural network learning?” The system walks back up the prerequisite chain and checks the student's knowledge model:
Concept
Student's mastery
Neural Networks
80%
Gradient Descent
65%
Derivatives
30%  — too weak
The AI realises: “You probably need to strengthen derivatives first.” So instead of randomly handing out another neural-network question, it teaches the path in order — Derivatives → Chain Rule → Gradient Descent → Neural Networks. That is personalized learning.
2.6  What happens when you upload a PDF
Suppose you upload Machine Learning.pdf. The system extracts two things. First, the text: “Gradient descent is an optimization algorithm…” Second, the images and diagrams. If a slide contains a loss surface with an arrow pointing to the minimum, a vision model reads the diagram and stores a description with its source, for example:
Image:  "Gradient descent moving down a loss
         surface toward the minimum."
Source: Slide 14
So if the student later asks “Explain the graph on slide 14,” the AI can actually retrieve and describe that diagram — not just the surrounding text.
2.7  What happens with a lecture video
Suppose the student uploads ML Lecture.mp4. The system uses Whisper to convert the speech to text, but it does not make one giant transcript. It keeps timestamps for each segment:
00:10  ->  Introduction
02:35  ->  Derivatives
07:20  ->  Chain Rule
12:41  ->  Gradient Descent
18:05  ->  Learning Rate
So when the AI answers “What is gradient descent?” it can point to a precise moment: [Lecture 2 @ 12:41]. Clicking that citation could jump the student straight to that part of the video. This is one of the strongest demo moments.
2.8  The “honest AI” feature
This one matters a lot. Suppose the student asks: “Explain quantum computing.” But the uploaded course material says nothing about quantum computing. A normal ChatGPT-style system might answer anyway. Our tutor says instead:
“This topic is not covered in your uploaded course material.”
That refusal is a feature, not a failure. We can also allow: “I can explain it using outside knowledge, but this information is not from your course material” — and clearly label it as outside knowledge. This demonstrates grounding and honesty, and judges immediately understand why it matters.
2.9  The quiz system — and why we verify every question
A normal AI might generate “Q: What is gradient descent?” and drop it straight into the quiz. We do not trust the first AI. Instead:
Generator — AI #1 writes the question and its answer.
Verifier — AI #2 independently checks it against the source material: “Is this question correct according to the lecture?”
Numerical check — if the question needs a calculation (for example 2 + 5 × 3), Python computes it independently.
Keep only verified questions — a question is stored only if the checks pass.
Generated
    |
Verified?
   / \
 NO   YES
 |      |
Reject  Store
So every question carries a badge, for example:
Verified    : yes
Source      : Slide 14
Topic       : Gradient Descent
Difficulty  : Medium
2.10  Why verified questions matter
Imagine the AI generates one wrong question. Without verification the damage spreads: a wrong question leads to a wrong evaluation, which feeds a wrong mastery estimate, which produces bad personalization. Everything downstream becomes garbage. Our verification step stops that chain at the first link — a question reaches the student only if it is correct.
2.11  The learner model: how much does the student actually know?
We use a method called Bayesian Knowledge Tracing (BKT). Do not be put off by the name — the idea is simple: every concept has a mastery score, and the system updates those scores whenever the student answers a question.
Concept
Mastery
Derivatives
30%
Chain Rule
45%
Gradient Descent
70%
Neural Networks
80%
A worked example
Suppose Chain Rule mastery is 30% and the student answers a question correctly. The system does not jump to “100% — you know it!” The student might have guessed. So the model weighs four things: the current mastery, the chance of guessing, the chance of slipping up, and the chance of learning from this question. The score moves like this:
Correct answer:   30%  ->  66%  ->  71%
Wrong answer:     30%  ->   5%  ->  19%
The important idea: a correct answer raises our confidence that the student knows the concept, but it never proves mastery. And if the student answers wrongly, the estimate drops and the tutor responds — with an explanation, a simpler question, an example, and then another question.
2.12  How personalization happens
This is the really cool part. Suppose the student's knowledge looks like this:
Concept
Mastery
Derivatives
30%  — weak
Chain Rule
45%  — weak
Gradient Descent
75%  — fine
Neural Networks
80%  — fine
The system should not keep asking “What is a neural network?” — the student already knows it. Instead it runs this loop:
Find weakest concept
       |
Check prerequisites
       |
Teach prerequisite if necessary
       |
Generate an appropriate question
       |
Update mastery
Think of it like a skill tree in a game. One student's tree might show Chain Rule as the weak node, so the AI says “Let's practise Chain Rule before moving on.” Another student might already be strong there, so the tutor skips the basics for them. Same course, different teaching path — that is personalization.
2.13  The diagnostic test
When a new student joins, we know nothing about them. So we give roughly 8 questions spread across the top-level topics. Their answers set the initial mastery estimates, and the tutor already has a rough map of their strengths and weaknesses before the real teaching begins.
2.14  The forgetting curve
One more nice feature. Suppose a student learned derivatives and mastery was 90%. If they do not revisit it for two months, the system should not assume it stays at 90% forever. Mastery decays over time:
90%  ->  85%  ->  77%  ->  68%
So eventually the tutor can say: “You haven't reviewed derivatives recently. Let's revise it.” This is what turns the learner model into a study schedule.
2.15  What the final dashboard looks like
+----------------------------+
|        MY LEARNING         |
+----------------------------+
| Overall Mastery      72%   |
| Questions Answered   48    |
| Verified Questions   46    |
+----------------------------+
| Derivatives        [###..] 35%
| Chain Rule         [####.] 62%
| Gradient Descent   [#####] 81%
| Neural Networks    [#####] 89%
+----------------------------+
| Weakest:  Chain Rule       |
| Next:     Practise Chain   |
|           Rule             |
+----------------------------+
2.16  How we prove the system actually works
This is something many hackathon teams forget. We do not just claim “our AI personalizes learning” — we measure it. We create simulated students (weak, average, strong) and run two systems side by side: random question selection versus our adaptive tutor.
               Session 1    Session 5
Random            35%          47%
Adaptive          35%          72%
Now we have evidence: “Our adaptive selection improved simulated mastery compared with random question selection.” That is far stronger than “our AI is personalized.” The numbers above are illustrative — the real ones must come from our own experiments, and we will report them honestly, including the cases where retrieval failed.
Alongside this we use RAGAS to evaluate the retrieval-and-answer pipeline, reporting faithfulness (did the AI answer from the retrieved information?), answer relevancy (did it actually answer the question?), context precision (did it retrieve useful sources?) and context recall (did it retrieve everything needed?).
2.17  The complete architecture
Putting it all together:
          STUDENT MATERIAL
      PDF      Slides      Video
        \        |        /
         MULTIMODAL EXTRACTION
          (text + images)
                |
          KNOWLEDGE GRAPH
     (concepts, prerequisites, evidence)
                |
            RAG RETRIEVAL
            /          \
        TUTOR          QUIZ
         |           Generator
         |              |
         |           Verifier
         |              |
         |        Verified Question
          \            /
          STUDENT ANSWER
                |
         LEARNER MODEL (BKT)
                |
          UPDATED MASTERY
                |
         NEXT BEST CONCEPT
                |
           NEXT QUESTION
2.18  Why this is not “chat with PDF”
This is the most important thing to understand for the pitch. A chat-with-PDF project is a single straight line: PDF → retrieval → chatbot. Ours is a full learning system:
Chat with PDF:   PDF  ->  RAG  ->  Chatbot

Our system:      PDF + Video + Slides
                     ->  Multimodal extraction
                     ->  Concept + prerequisite graph
                     ->  Evidence-grounded RAG
                     ->  Verified assessment
                     ->  Learner model
                     ->  Personalized learning path
                     ->  Measured improvement
We are not building another chatbot. We are building a learning system — and that is the sentence to memorise for the judges.
2.19  What to build first — the priority order
Do not try to build every feature perfectly. Build in this order and stop when time runs out:
Knowledge graph — concept, prerequisite and evidence links. Example: Derivatives → Chain Rule → Gradient Descent.
Grounded tutor — answers questions and shows “Source: Slide 14”, and says “not covered in your material” when it isn't.
Verified quiz — generate → verify → check source → store, with a “Verified” badge.
BKT learner model — keep it simple: concept → mastery probability, updated after every answer.
Adaptive recommendation — show the judge: “your weakest prerequisite is Chain Rule; recommended next question: Chain Rule, medium.” This makes personalization visible.
2.20  The “wow” features, if time allows
Video timestamp citations — [Lecture 3 @ 12:41], click to jump.
Diagram understanding — [Slide 14 — gradient descent diagram].
Hindi mode — “Explain this in Hindi” for English lectures.
Weak-topic flashcards — “here are 5 flashcards based on your weakest concepts.”
Course flow map — Unit 1 → Unit 2 → Unit 3 → Unit 4.
2.21  The demo tells a story
Do not spend five minutes showing code. Show this instead:
Scene 1 — Upload: a PDF, a slide deck and a lecture video. Show “building your course knowledge graph…”
Scene 2 — The graph appears: Derivatives → Chain Rule → Gradient Descent → Neural Networks.
Scene 3 — Ask a question: “Explain gradient descent.” The answer arrives with [Slide 14]; click it and show the exact source.
Scene 4 — Try to trick it: ask “Explain quantum computing” and watch the refusal. This is an excellent demo moment.
Scene 5 — Diagnostic: the student answers 8 questions; the dashboard shows weak and strong topics.
Scene 6 — Adaptive learning: the system names the weakest prerequisite and generates a verified question with topic, source and difficulty.
Scene 7 — Results: show random 47% versus adaptive 72% and close with “we don't just claim personalization, we measure it.”
2.22  The simplest mental model
If you forget everything else, remember these five boxes:
COURSE MATERIAL
      |
KNOWLEDGE GRAPH
      |
VERIFIED RAG
      |
VERIFIED QUIZ
      |
LEARNER MODEL
      |
PERSONALIZED NEXT STEP
And the system loops forever: teach → ask → evaluate → update mastery → find weakness → teach the next concept. That loop is the actual innovation. The AI is not merely saying “here is an answer.” It is saying: “here is the answer, here is exactly where I got it, here is whether the question is verified, here is what you currently understand, and here is what you should learn next.”
2.23  Practical reference: the shared data contract
Because everything runs on the graph, we freeze three shapes on day one so all four of us can build in parallel. These are the exact objects we pass around.
// 1. Content Unit  - one chunk of source material
{ unit_id, source_id, source_type: 'video'|'pdf'|'slides',
  location: { page | slide | timestamp },
  text, image_caption?, embedding, topic_ids[] }

// 2. Concept Node  - one idea in the graph
{ concept_id, name, topic, prerequisites: [concept_id],
  evidence_units: [unit_id] }

// 3. Question  - one assessment item
{ q_id, topic, source_location, difficulty: 1-5,
  type: 'mcq'|'short'|'numeric', stem, options?, answer,
  verified: bool, verifier_agreement, embedding }
2.24  Practical reference: build vs. stub vs. slide
Our biggest risk is scope — the plan above is a month of work; a hackathon is a day or two. So we build one narrow slice flawlessly and present the rest as clearly-labelled next steps. The left column must work in the live demo; the middle is “coming next”; the right is vision, not a claim.
Build for real (must run live)
Stub or fake
Slides only
One modality done well: PDF or slides, with figure captioning
Second modality (video)
Full multimodal
Concept graph for one topic, with validated edges
Whole-course graph
Course flow map
Verified quiz pipeline (generator → verifier → Python check)
De-dupe at scale
Flashcard generator
BKT learner model + adaptive next-question
Forgetting curve
Study-schedule feature
Claim-level citations + refusal
Hindi mode
—
Simulated-student adaptive-vs-random chart
—
—
Pick one real course (an NPTEL or MIT OpenCourseWare lecture series) as the demo material. Judges trust depth on real content far more than a generic “upload anything” claim, and it makes the graph quality checkable.
2.25  Practical reference: the rubric map
When a judge can tick their own rubric boxes while watching us, we have removed all their cognitive work. We will show this table on screen.
Criterion
Our feature
Evidence we show
Grounding (20%)
Claim-level citations + confidence-gated refusal
Click a chip, it jumps to the exact slide/timestamp; a live refusal
Assessment (15%)
Generator → independent verifier → Python check
Verification badge on each question; de-dup rate
Personalization (20%)
BKT mastery + adaptive selection
Mastery dashboard; adaptive-vs-random baseline chart
Evaluation (15%)
RAGAS + team test set
Faithfulness, relevancy, context precision/recall, refusal accuracy
UX & Demo (15%)
Dashboard + guided workflow
Clean 3–10 min walkthrough
Technical (15%)
One shared graph, clean services
Architecture diagram
Part 3 — Dividing the Work Across Four Members
3.1  The shape of the split
We split into four vertical pods. Each member owns one part end-to-end and is the only person who edits their module. Everything is exchanged through the three shared schemas from section 2.23 and a common FastAPI service, so no pod blocks another. One person (Pod D) is also the integration owner.
Pod A — Ingestion & Multimodal Extraction: turn raw videos, PDFs and slides into Content Units with locations and figure captions.
Pod B — Concept Graph, Retrieval & Grounding: build the graph, run hybrid search, produce citations and refusals.
Pod C — Assessment & Learner Model: generate and verify questions, run BKT, produce the misconception report.
Pod D — Frontend, Evaluation & Demo: the dashboard and chat UI, the RAGAS harness, simulated students, and the demo video.
3.2  Who owns what
Member
Owns (only they edit it)
Key outputs
Depends on
Member A
Ingestion & multimodal extraction
PDF/slide parser; Whisper + keyframes; vision captioning; embeddings; vector store loaded
Schemas frozen
Member B
Concept graph, retrieval, grounding
Topic/concept/prerequisite extraction; hybrid search + reranker; citation chips; refusal threshold; claim-level attribution
Content Units from A
Member C
Assessment & learner model
Quiz generator; verifier + Python check; de-dup; BKT engine; adaptive selector; misconception report
Concept Nodes from B
Member D
Frontend, evaluation, demo
Streamlit/Next.js UI; mastery dashboard; RAGAS harness; simulated students + baseline; demo video; integration
All pods
3.3  Rules that keep us unblocked
Freeze the three schemas in the first hour. Any change after that is announced in the group chat, never made silently.
Everyone can start immediately using mock data: Pod D builds the UI against fake Content Units, Pod C builds BKT against fake questions, Pod B builds the graph against fake text. Real data slots in later.
One shared repo, one branch per member, pull requests reviewed by the integration owner.
Every pod writes one small test for its own piece before integration day, so we can tell whose part broke.
3.4  Suggested timeline
Phase
What happens
Phase 0 (first 1–2 hrs)
Set up the repo and environment; freeze the three schemas; choose the course material; sketch the UI wireframe.
Phase 1
Each pod builds its core against mock data. First internal checkpoints.
Phase 2
Integrate on real material; get the first end-to-end path working: upload → ask → cited answer.
Phase 3
Wire in assessment, the learner model, the dashboard, and the evaluation harness. Run simulated students.
Phase 4
Hard feature freeze. Record the demo video, write the documentation, tidy the architecture diagram.
Hard rule: freeze features before recording. Live demos break; we record a fallback run so the video is never at the mercy of the network.
3.5  Demo-video ownership
Each member narrates the part they built — it sounds authentic and spreads the workload. One person (Pod D) edits and uploads. The running order follows section 2.21: build the graph on screen, click a citation, trigger a refusal, take the diagnostic, show mastery, generate a verified quiz, then show the adaptive-vs-random chart and the architecture diagram.
Part 4 — Tools & Stack
Choices are biased toward fast setup and toward things that already work in a hackathon sandbox. Where two options are given, the first is the faster one.
Layer
Choice
Why
Frontend
Streamlit (fast) or Next.js
Streamlit gets a usable dashboard in hours; Next.js if we want polish.
Backend
FastAPI
Lightweight Python API; plays well with every model library.
Vector store
Chroma (fast) or Qdrant
Hybrid search = BM25 + embeddings, then a cross-encoder reranker.
Graph
NetworkX, drawn with D3 or Cytoscape
Simple to build, easy to render as the course flow map.
Transcription
Whisper (or faster-whisper)
Timestamps for video citations.
Vision
Gemini or GPT-4o-class model
Captions and structured descriptions of diagrams and figures.
LLMs
One for generation, a different one for verification
Two models must not share the same blind spot.
Numerical check
Python + SymPy
Executes numeric answers so the answer key is provably correct.
Embeddings
sentence-transformers
Local, free, good enough for retrieval and de-duplication.
Evaluation
RAGAS (DeepEval/TruLens as backup)
Faithfulness, answer relevancy, context precision/recall out of the box.
Indian-language mode
Sarvam APIs (optional extra)
Cheap Hindi explanations for English lectures — fits an Indian hackathon.
4.1  What to avoid
Trying every optional feature. Depth on grounding + assessment + personalization (55% of the score) beats breadth.
Unverified quiz questions. One wrong answer key damages both the learner model and the judges' trust.
Showing only good results. Include the cases where retrieval failed and say what we did about it — the rubric explicitly rewards honesty.
Leaving integration to the last minute. The end-to-end path is the deliverable; build it early and grow it.
Source: requirements and evaluation criteria restated from the hackathon's Track D problem statement document.