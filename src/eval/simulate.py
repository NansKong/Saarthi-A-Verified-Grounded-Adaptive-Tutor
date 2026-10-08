"""
simulate.py  --  The simulated-student evaluation.

We cannot test on real students during a hackathon, so we invent them and run
them through our system, then compare two conditions:

    RANDOM    -- pick questions at random          (the baseline)
    ADAPTIVE  -- pick questions with our selector  (the thing we're testing)

Each simulated student has a HIDDEN true ability per concept, and the abilities
DIFFER across concepts -- every student is strong at some topics and weak at
others. They answer correctly with a probability based on true ability (plus a
chance of guessing), and practising a concept slowly improves true ability,
with diminishing returns, so weak concepts have more room to grow.

What we measure
---------------
* Concepts mastered (>= 0.60) -- the headline. Adaptive selection aims at the
  weak concepts, so more of them get lifted over the mastery line. Random
  selection wastes effort on topics the student has already mastered.
* Mean true mastery gain -- the total, reported honestly (the two conditions do
  the same amount of work, so this is close).
* Question repetition rate -- de-duplication keeps this at 0%.

One run of one student is noisy, so we average over many students per profile
(a Monte Carlo run). That is the honest way to measure the effect.

--- Run it ---
    python -m src.eval.simulate
"""

import random
from statistics import mean

from src.schemas.models import Question
from src.mock_data import get_question_concept_id
from src.learner_model.bkt import LearnerModel
from src.learner_model.adaptive import build_quiz

SESSIONS = 5          # sessions per student
QUIZ_SIZE = 6         # questions per session
STUDENTS = 40         # simulated students per profile (Monte Carlo)
SEED = 42             # fixed seed so the run is reproducible
LEARN_GAIN = 0.07     # how fast practising a concept improves true ability
MASTERY = 0.60        # a concept counts as "mastered" at this level
GUESS = 0.20
SLIP = 0.10

# Base true ability per concept (in concept order). Each profile has a few WEAK
# topics mixed with topics the student has already mastered. This is the case
# where tutoring matters most: random selection wastes questions on the mastered
# topics, while adaptive selection spends them on the weak ones.
PROFILES = {
    "weak":    [0.10, 0.15, 0.20, 0.85, 0.20, 0.90],
    "average": [0.45, 0.50, 0.25, 0.90, 0.90, 0.85],
    "strong":  [0.85, 0.90, 0.80, 0.25, 0.90, 0.85],
}


class SimulatedStudent:
    """A fake student with hidden true ability per concept."""

    def __init__(self, true_ability):
        self.true = dict(true_ability)

    def answer(self, concept_id, rng):
        p = self.true[concept_id]
        p_correct = p * (1 - SLIP) + (1 - p) * GUESS
        return rng.random() < p_correct

    def learn(self, concept_id):
        self.true[concept_id] += LEARN_GAIN * (1 - self.true[concept_id])


def make_pool(concepts, per_difficulty=4):
    pool = []
    for c in concepts:
        for d in range(1, 6):
            for i in range(per_difficulty):
                pool.append(Question(
                    q_id=f"sim_{c.concept_id}_{d}_{i}",
                    topic=c.topic,
                    source_location={"slide": 0},
                    difficulty=d,
                    type="mcq",
                    stem=f"[{c.name} / difficulty {d}]",
                    options=["a", "b", "c", "d"],
                    answer="a",
                    verified=True,
                    verifier_agreement=1.0,
                ))
    return pool


def run_one(true_ability, concepts, pool, condition, rng):
    """One simulated student through SESSIONS sessions."""
    student = SimulatedStudent(true_ability)
    model = LearnerModel([c.concept_id for c in concepts])
    start = mean(true_ability.values())
    used, asked = set(), []

    for _ in range(SESSIONS):
        if condition == "adaptive":
            quiz = build_quiz(concepts, model.all_masteries(), pool, used_ids=used, size=QUIZ_SIZE)
        else:
            available = [q for q in pool if q.q_id not in used]
            quiz = rng.sample(available, min(QUIZ_SIZE, len(available)))
        for q in quiz:
            used.add(q.q_id)
            asked.append(q.q_id)
            concept_id = get_question_concept_id(q)
            ok = student.answer(concept_id, rng)
            model.observe(concept_id, ok)
            student.learn(concept_id)

    return {
        "mastered": sum(1 for v in student.true.values() if v >= MASTERY),
        "true_gain": mean(student.true.values()) - start,
        "final_estimate": mean(model.all_masteries().values()),
        "repetition": 1 - len(set(asked)) / len(asked),
    }


def run_profile(base_abilities, concepts, pool):
    """Average many students (with small random variation) under both conditions."""
    out = {"random": [], "adaptive": []}
    for s in range(STUDENTS):
        rng = random.Random(SEED + s)
        true_ability = {
            c.concept_id: min(0.95, max(0.05, base_abilities[i] + rng.uniform(-0.05, 0.05)))
            for i, c in enumerate(concepts)
        }
        for cond in ("random", "adaptive"):
            out[cond].append(run_one(true_ability, concepts, pool, cond, random.Random(SEED + s)))
    keys = ("mastered", "true_gain", "final_estimate", "repetition")
    return {k: {c: mean(r[k] for r in out[c]) for c in out} for k in keys}


def main():
    from src.mock_data import get_concepts
    concepts = get_concepts()
    pool = make_pool(concepts)
    n = len(concepts)

    print("=" * 72)
    print("SIMULATED-STUDENT EVALUATION")
    print(f"{STUDENTS} students per profile | {SESSIONS} sessions x {QUIZ_SIZE} questions each")
    print(f"A concept counts as mastered at >= {MASTERY}")
    print("=" * 72)

    results = {name: run_profile(ab, concepts, pool) for name, ab in PROFILES.items()}

    print(f"{'Profile':<9}{'Condition':<11}{'Concepts mastered':<20}{'Mean true gain':<17}{'Final estimate':<16}{'Repeat'}")
    print("-" * 72)
    for name in PROFILES:
        r = results[name]
        for cond in ("random", "adaptive"):
            print(f"{name:<9}{cond:<11}"
                  f"{format(r['mastered'][cond], '.1f') + f' / {n}':<20}"
                  f"{'+' + format(r['true_gain'][cond], '.3f'):<17}"
                  f"{format(r['final_estimate'][cond], '.2f'):<16}"
                  f"{format(r['repetition'][cond], '.0%')}")
        gap = r["mastered"]["adaptive"] - r["mastered"]["random"]
        print(f"{'':<20}-> adaptive masters +{gap:.1f} more concepts than random")
        print("-" * 72)

    print("=" * 72)
    print("Honest note: these are SIMULATED students, averaged over many runs. The")
    print("gain shows the learner model and selector behave correctly -- not that")
    print("they work on real people. Total gain is close between conditions because")
    print("both ask the same number of questions; the difference is WHICH concepts")
    print("get fixed -- adaptive lifts the weak ones over the line.")


if __name__ == "__main__":
    main()
