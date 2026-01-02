TYPE2_PROMPT = """
You are reviewing code changes.

Your job is to point out ONE concrete problem and ONE concrete fix.
Do NOT explain benefits.
Do NOT repeat rules.
Do NOT give general advice.

Context:
File: {file}
Layer: {layer}
Signals: {signals}

Changed code:
{diff}

Respond ONLY in this format:

ISSUE:
<single sentence>

CAUSE:
<optional, single short sentence>

ACTION:
- Extract <function_name>(<params>) to <target_file_or_layer>

"""
