# services/layer_policy.py

LAYER_POLICIES = {
    "domain": {
        "allow_local_fixes": False,
        "must_move_on": [
            "ADAPTER_CALL",
            "WORKFLOW_ORCHESTRATION",
            "IO_OPERATION",
        ],
        "forbidden_suggestions": [
            "try",
            "except",
            "wrap",
            "handle exception",
            "add validation",
            "guard clause",
        ],
        "allowed_actions": [
            "move_to_service",
            "move_to_workflow",
            "extract_interface",
        ],
    },

    "services": {
        "allow_local_fixes": True,
        "must_move_on": [],
        "forbidden_suggestions": [],
        "allowed_actions": [
            "extract_function",
            "split_service",
            "rename_function",
            "reduce_responsibility",
        ],
    },

    "workflows": {
        "allow_local_fixes": True,
        "must_move_on": [
            "BUSINESS_LOGIC",
            "VALIDATION_LOGIC",
        ],
        "forbidden_suggestions": [],
        "allowed_actions": [
            "move_to_service",
            "extract_step",
        ],
    },

    "adapters": {
        "allow_local_fixes": False,
        "must_move_on": [
            "BUSINESS_LOGIC",
        ],
        "forbidden_suggestions": [
            "add business rule",
            "add validation",
        ],
        "allowed_actions": [
            "move_to_service",
            "thin_adapter",
        ],
    },
}

def violates_layer_policy(insight: dict, layer: str) -> bool:
    policy = LAYER_POLICIES[layer]
    action = insight["action"].lower()

    for forbidden in policy["forbidden_suggestions"]:
        if forbidden in action:
            # print(f"Disallowed suggestion detected for layer {layer}: {forbidden} in action '{action}'")
            return True

    return False
