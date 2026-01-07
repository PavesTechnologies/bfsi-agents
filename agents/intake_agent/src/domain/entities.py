



def building_entity_from_file(file_path):
    text = file_path.read_text()
    for line in text.splitlines():
        cleaned_line = extract_text(line)
        # Further processing to build entitys
        cleaned_line.strip()

    return cleaned_line

def process_application(data):
    result = {}

    if data.get("a"):
        if data["a"] > 10:
            if data["a"] < 100:
                result["a"] = data["a"] * 2
            else:
                result["a"] = data["a"] / 2
        else:
            result["a"] = 0
    else:
        result["a"] = None

    if data.get("b"):
        for x in data["b"]:
            if x % 2 == 0:
                result.setdefault("b", []).append(x * 2)
            else:
                result.setdefault("b", []).append(x + 1)

    if data.get("c"):
        try:
            result["c"] = int(data["c"])
        except Exception:
            result["c"] = 0

    return result


def review_with_llm(contexts: List[dict]) -> List[dict]:
    insights = []

    for ctx in contexts:
        layer = ctx["layer"]

        policy = LAYER_POLICIES[layer]
        
        # prompt = TYPE2_PROMPT.format(
        #     architecture_contract=ctx["architecture_contract"],
        #     file=ctx["file"],
        #     layer=layer,
        #     signals=ctx["signals"].__str__(),
        #     primary_signal=ctx["primary_signal"],
        #     diff=ctx["diff"][:3000],
        #     allow_local_fixes=str(policy['allow_local_fixes']),
        #     allowed_actions="\n  ".join(policy['allowed_actions']),
        #     forbidden_suggestions="\n  ".join(policy['forbidden_suggestions']),
        # )

        prompt = TYPE2_XML_PROMPT.format(
        file=ctx["file"],
        layer=layer,
        primary_signal=ctx["primary_signal"],
        signals=str(ctx["signals"]),
        diff=ctx["diff"][:3000],
        allow_local_fixes=str(policy["allow_local_fixes"]),
        allowed_actions="\n".join(
            f"      <ACTION>{a}</ACTION>" for a in policy["allowed_actions"]
        ),
        forbidden_suggestions="\n".join(
            f"      <SUGGESTION>{s}</SUGGESTION>" for s in policy["forbidden_suggestions"]
        ),
    )




        # print(f"-----------------------------\nLLM Prompt for {ctx['file']}:\n{prompt}\n---\n")

        raw = ask_llm(prompt)

        # print(f"LLM Response for {ctx['file']}:\n{raw}\n---\n")

        parsed = parse_llm_output(raw)
        if not parsed:
            print(f"Failed to parse LLM output for {ctx['file']}:\n{raw}")
            continue  # discard junk / NONE / malformed

        
        if violates_layer_policy(parsed, layer):
            print(f"Disallowed suggestion detected for layer {layer}: {parsed['action']}")
            continue

        insights.append(
            {
                "file": ctx["file"],
                "issue": parsed["issue"],
                "action": parsed["action"],
                "line": ctx["primary_line"],

            }
        )

    return insights
