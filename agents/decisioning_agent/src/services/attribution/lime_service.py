"""Optional LIME attribution hook for future learned scoring models."""


def compute_lime_attribution(*args, **kwargs):
    raise NotImplementedError(
        "LIME attribution is not enabled for the current deterministic underwriting engine."
    )
