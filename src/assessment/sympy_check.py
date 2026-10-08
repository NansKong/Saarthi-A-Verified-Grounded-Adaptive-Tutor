"""
sympy_check.py  --  The third check for numerical questions.

The pipeline for a NUMERIC question has three independent checks:

  1. Groq writes the question and its answer.
  2. Gemini solves it independently and agrees.
  3. SymPy COMPUTES the answer from the underlying maths.   <-- this file

A numeric answer key is trusted only when all three agree. SymPy is the
strongest check because it does not guess -- it calculates.

How the maths is supplied: for a numeric question, the generator also returns
the expression to evaluate (and any values to substitute), e.g.

    { "expr": "diff(3*x**2, x)", "subs": {"x": 2} }   ->  12

--- Run it ---
    python sympy_check.py
"""

import sympy
from sympy import symbols, diff
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
)

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)
LOCAL_DICT = {"x": symbols("x"), "y": symbols("y"), "diff": diff, "symbols": symbols}


def evaluate(expression, subs=None):
    """Parse a maths expression and compute its numeric value."""
    expr = parse_expr(str(expression), local_dict=LOCAL_DICT, transformations=TRANSFORMS)
    if subs:
        expr = expr.subs({symbols(k): v for k, v in subs.items()})
    return float(sympy.N(expr))


def check_numeric(expression, subs, claimed_answer, tol=1e-6):
    """Return (ok, computed_value, claimed_value). ok=True means they match."""
    computed = evaluate(expression, subs)
    try:
        claimed = float(str(claimed_answer).strip())
    except (TypeError, ValueError):
        return False, computed, None
    return abs(computed - claimed) <= tol, computed, claimed


# demo: the numeric questions from the mock bank, paired with their maths
DEMO = [
    ("q2", "If f(x) = 3x^2, what is f'(2)?",
     {"expr": "diff(3*x**2, x)", "subs": {"x": 2}}, "12"),
    ("q4", "If y = (2x + 1)^3, what is dy/dx at x = 0?",
     {"expr": "diff((2*x+1)**3, x)", "subs": {"x": 0}}, "6"),
    ("q8", "With learning rate 0.1 and gradient 5, what is the update step size?",
     {"expr": "0.1*5", "subs": {}}, "0.5"),
]


def main():
    print("=" * 60)
    print("SYMPY CHECK  --  computing numeric answers independently")
    print("=" * 60)
    for qid, stem, spec, claimed in DEMO:
        ok, computed, _ = check_numeric(spec["expr"], spec.get("subs"), claimed)
        print(f"[{'MATCH' if ok else 'MISMATCH'}] {qid}: {stem}")
        print(f"          expression : {spec['expr']}   subs={spec.get('subs')}")
        print(f"          SymPy says : {computed}    answer key: {claimed}")
    print("-" * 60)
    print("Catching a wrong answer key on purpose:")
    ok, computed, _ = check_numeric("diff(3*x**2, x)", {"x": 2}, "15")
    print(f"  diff(3*x**2, x) at x=2 -> SymPy={computed}, key=15 -> "
          f"{'MATCH' if ok else 'MISMATCH (rejected)'}")
    print("-" * 60)
    print("Done. A numeric question is kept only if Groq, Gemini AND SymPy agree.")


if __name__ == "__main__":
    main()
