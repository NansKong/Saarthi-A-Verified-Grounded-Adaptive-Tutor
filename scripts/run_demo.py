"""
run_demo.py  --  Run this to see Pod C working.

  python -m scripts.run_demo

It prints three things:
  1. The BKT worked example from the plan doc (30% -> 66% -> 71%, and 30% -> 5% -> 19%).
  2. A new student's diagnostic setting initial mastery.
  3. An adaptive quiz being built, and mastery updating after each answer.
"""

from src.mock_data import get_concepts, get_questions, get_question_concept_id
from src.learner_model.bkt import LearnerModel, BKTParams
from src.learner_model.adaptive import (
    select_next_concept,
    choose_difficulty,
    build_quiz,
)

concepts = get_concepts()
questions = get_questions()


def line():
    print("-" * 60)


def pct(x):
    return f"{x*100:5.1f}%"


print("=" * 60)
print("POD C DEMO  --  Assessment & Learner Model")
print("=" * 60)

# --- 1. BKT worked example (matches the plan doc exactly) ---
print("\n[1] BKT worked example on the concept 'Chain Rule'")
line()
m = LearnerModel(["chain_rule"], BKTParams(prior=0.30, guess=0.20, slip=0.10, learn=0.15))
print(f"  start (prior)                 : {pct(m.mastery('chain_rule'))}")
m2 = LearnerModel(["chain_rule"], BKTParams(prior=0.30, guess=0.20, slip=0.10, learn=0.15))
m2.observe("chain_rule", True)
print(f"  after a CORRECT answer        : {pct(m2.mastery('chain_rule'))}  (expect ~71%)")
m3 = LearnerModel(["chain_rule"], BKTParams(prior=0.30, guess=0.20, slip=0.10, learn=0.15))
m3.observe("chain_rule", False)
print(f"  after a WRONG answer          : {pct(m3.mastery('chain_rule'))}  (expect ~19%)")
print("  note: one correct answer is weak evidence -- guessing is possible.")

# --- 2. Diagnostic for a brand-new student ---
print("\n[2] A new student takes the 8-question diagnostic")
line()
student = LearnerModel([c.concept_id for c in concepts], BKTParams())
# pretend they answer the four top-level concepts; wrong on the easy prerequisite
diagnostic = {"derivatives": False, "loss_function": True,
              "chain_rule": False, "gradient_descent": True}
student.apply_diagnostic(diagnostic)
for c in concepts:
    print(f"  {c.name:<18} {pct(student.mastery(c.concept_id))}")

# --- 3. Adaptive quiz + mastery updates ---
print("\n[3] Building an adaptive quiz (5 questions) from the current mastery")
line()
masteries = student.all_masteries()
quiz = build_quiz(concepts, masteries, questions, size=5)
for i, q in enumerate(quiz, 1):
    print(
        f"  Q{i}: [{get_question_concept_id(q):<16}] "
        f"diff {q.difficulty}  {q.stem[:52]}"
    )

print("\n[4] Student answers the quiz; mastery updates after every answer")
line()
# simulate: they get the prerequisite right, then most others right
answers = [True, True, True, False, True]
for q, correct in zip(quiz, answers):
    concept_id = get_question_concept_id(q)
    before = student.mastery(concept_id)
    student.observe(concept_id, correct)
    after = student.mastery(concept_id)
    tag = "correct" if correct else "WRONG  "
    print(f"  {tag}  {concept_id:<16} {pct(before)} -> {pct(after)}")

print("\n[5] What the tutor recommends next")
line()
nxt = select_next_concept(concepts, student.all_masteries())
print(f"  weakest ready concept  : {nxt}")
print(f"  suggested difficulty   : {choose_difficulty(student.mastery(nxt))}")
print("\nFinal mastery board:")
for c in concepts:
    bar = "#" * int(student.mastery(c.concept_id) * 20)
    print(f"  {c.name:<18} {pct(student.mastery(c.concept_id))}  {bar}")
line()
print("Done. This is the learner-model core; the quiz generator + verifier plug in next.")
