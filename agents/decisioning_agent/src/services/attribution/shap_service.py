"""Optional SHAP attribution hook for future learned scoring models."""


def compute_shap_attribution(*args, **kwargs):
    raise NotImplementedError(
        "SHAP attribution is not enabled for the current deterministic underwriting engine."
    )
