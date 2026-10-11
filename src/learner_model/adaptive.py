"""
adaptive.py  --  Choosing the next concept to ask about.

Decision 5 (topic -> question mapping): each quiz is 5 questions; questions
have difficulty 1..5; difficulty is chosen to match mastery (start easy when
mastery is low, harder as it rises). A diagnostic is 8 questions spread over
the top-level topics.

The selection rule (from the plan doc, section 2.12):
  1. Eligible concepts = those whose prerequisites are ALL above a threshold
     (Decision: threshold = 0.60).
  2. Ask about the eligible concept with the LOWEST mastery.
  3. If nothing is eligible, back up and target the weakest prerequisite.
"""

from src.mock_data import get_question_concept_id

PREREQ_THRESHOLD = 0.60   # Decision: a prerequisite counts as "ready" at 0.6
QUIZ_SIZE = 5             # Decision: 5 questions per quiz
DIAGNOSTIC_SIZE = 8       # Decision: 8 questions for a new student


def select_next_concept(concepts, masteries, threshold=PREREQ_THRESHOLD):
    """Return the concept_id the student should be asked about next."""
    def prereqs_ready(c):
        return all(masteries.get(p, 0.0) >= threshold for p in c.prerequisites)

    eligible = [c for c in concepts if prereqs_ready(c)]
    if eligible:
        # lowest mastery among the concepts we are allowed to ask about
        return min(eligible, key=lambda c: masteries.get(c.concept_id, 0.0)).concept_id

    # No concept is ready -> the weakest prerequisite is the blocker. Target it.
    return min(concepts, key=lambda c: masteries.get(c.concept_id, 0.0)).concept_id


def choose_difficulty(mastery: float) -> int:
    """Map mastery (0..1) to a target difficulty (1..5). Weak -> easier questions."""
    if mastery < 0.30:
        return 1
    if mastery < 0.50:
        return 2
    if mastery < 0.70:
        return 3
    if mastery < 0.85:
        return 4
    return 5


def pick_questions_for_concept(questions, concept_id, target_difficulty, used_ids, n=1):
    """Pick up to n unused, verified questions for a concept, closest to the target difficulty."""
    pool = [q for q in questions
            if get_question_concept_id(q) == concept_id
            and q.verified
            and q.q_id not in used_ids]
    pool.sort(key=lambda q: abs(q.difficulty - target_difficulty))
    return pool[:n]


def build_quiz(
    concepts,
    masteries,
    questions,
    used_ids=None,
    size=QUIZ_SIZE,
    target_difficulty=None,
    target_concept=None,
):
    """Build a quiz: repeatedly pick concepts and questions tailored to mastery or user preferences.
    
    If target_difficulty (1-5) is provided, filters/prioritizes questions with that exact difficulty.
    If target_concept is provided, prioritizes questions belonging to that concept.
    """
    used_ids = set(used_ids or [])
    quiz = []
    local_masteries = dict(masteries)  # copy; we do not mutate the real model here

    # Filter pool by target_concept if requested
    concept_filtered_pool = questions
    if target_concept:
        concept_pool = [q for q in questions if get_question_concept_id(q) == target_concept]
        if concept_pool:
            concept_filtered_pool = concept_pool

    # If target_difficulty is given and we have questions with exact difficulty, prioritize them
    for _ in range(size):
        if target_concept:
            cid = target_concept
        else:
            cid = select_next_concept(concepts, local_masteries)

        diff = target_difficulty if target_difficulty is not None else choose_difficulty(local_masteries.get(cid, 0.0))
        picked = pick_questions_for_concept(concept_filtered_pool, cid, diff, used_ids, n=1)

        if not picked:
            # Fallback 1: any unused question in concept_filtered_pool closest to target difficulty
            remaining = [q for q in concept_filtered_pool if q.verified and q.q_id not in used_ids]
            if not remaining:
                # If exhausted, allow reusing from concept_filtered_pool
                remaining = [q for q in concept_filtered_pool if q.verified]
            if not remaining:
                # Fallback to any question in global questions
                remaining = [q for q in questions if q.verified]
            if not remaining:
                break
            remaining.sort(key=lambda q: abs(q.difficulty - diff))
            picked = [remaining[0]]

        q = picked[0]
        quiz.append(q)
        used_ids.add(q.q_id)
        local_masteries[cid] = min(1.0, local_masteries.get(cid, 0.0) + 0.05)
    return quiz


def build_diagnostic(concepts, questions, size=DIAGNOSTIC_SIZE, used_ids=None):
    """Build the new-student diagnostic: `size` questions spread across the topics.

    Round-robins over the distinct topics, taking one concept at a time, so the
    diagnostic samples every topic before it repeats any. This is what sets the
    starting mastery for a student with no history.
    """
    used = set(used_ids or [])
    topics = {}
    for c in concepts:
        topics.setdefault(c.topic, []).append(c)

    picks = []
    while len(picks) < size:
        progressed = False
        for bucket in topics.values():
            if len(picks) >= size:
                break
            while bucket:
                concept = bucket.pop(0)
                pool = [q for q in questions
                        if get_question_concept_id(q) == concept.concept_id
                        and q.verified and q.q_id not in used]
                if pool:
                    q = pool[0]
                    picks.append(q)
                    used.add(q.q_id)
                    progressed = True
                    break
        if not progressed:
            break
    return picks


if __name__ == "__main__":
    from src.mock_data import get_concepts, get_questions, get_question_concept_id
    concepts, questions = get_concepts(), get_questions()
    diag = build_diagnostic(concepts, questions)
    print(f"Diagnostic ({len(diag)} questions, spread across topics):")
    for i, q in enumerate(diag, 1):
        print(f"  Q{i}: [{get_question_concept_id(q):<16}] {q.stem}")
