"""Small hand-labelled retrieval set over the mock corpus: query -> acceptable unit_ids.
`lexical` queries share vocabulary with the source; `semantic` ones are paraphrases, where
real embeddings should beat the built-in fallback. Used by tests and scripts/retrieval_check.py.
"""
LEXICAL = [
    ("what is the chain rule", {"sl-08", "tb-0118", "vd-0440", "sl-09"}),
    ("how does learning rate affect convergence", {"sl-15", "tb-0209", "vd-1085"}),
    ("loss surface diagram showing steps downhill", {"sl-14"}),
    ("what is backpropagation", {"sl-22", "tb-0236", "vd-1380"}),
    ("why do we need activation functions", {"sl-20"}),
    ("mean squared error", {"sl-11"}),
    ("slope of the tangent line", {"sl-04", "vd-0155"}),
    ("stochastic gradient descent and mini-batch", {"sl-16"}),
    ("overfitting and regularization", {"sl-25"}),
    ("universal approximation theorem", {"tb-0231"}),
    ("gradient as vector of partial derivatives", {"tb-0204"}),
    ("gradient descent update rule", {"sl-13", "tb-0207"}),
    ("power rule for derivatives", {"sl-06"}),
    ("steps of the training loop", {"sl-23"}),
]
SEMANTIC = [
    ("why does my training loss blow up", {"sl-15", "vd-1085", "tb-0209"}),
    ("how do we compute gradients efficiently in a deep model", {"sl-22", "tb-0236", "vd-1380"}),
    ("what mistake do students make when differentiating nested functions", {"vd-0440"}),
    ("how do I know if the model is memorising the training data", {"sl-25"}),
    ("why can't we just stack linear layers", {"sl-20"}),
    ("analogy for walking down a hill in fog", {"vd-0761"}),
]
OFF_MATERIAL = [  # nothing to do with the course
    "explain quantum computing",
    "who won the football world cup",
    "how do I cook biryani",
    "what is the capital of France",
    "history of the Roman empire",
    "how do vaccines work",
    "best way to learn guitar",
    "what causes inflation in an economy",
    "how does photosynthesis work",
    "who wrote Hamlet",
]
NEAR_MISS = [  # right subject area, content NOT in the material: must not come back as a confident grounded answer
    "what is the derivative of sin x",
    "how does the transformer attention mechanism work",
    "explain the Adam optimizer",
    "what is a convolutional neural network",
]


def evaluate(retriever, items, k=3):
    """Returns (hit@k, MRR). A hit = any acceptable unit in the top k."""
    hits, rr = 0, 0.0
    for q, ok in items:
        ids = [h.unit.unit_id for h in retriever.search(q, k)]
        if any(i in ok for i in ids):
            hits += 1
        for rank, i in enumerate(ids, 1):
            if i in ok:
                rr += 1 / rank
                break
    n = len(items)
    return hits / n, rr / n
