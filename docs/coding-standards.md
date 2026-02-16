# Coding Standards

## Philosophy

These coding standards are intended to make the codebase easier to read, reason about, and maintain over time. Clear, consistent code reduces bugs, simplifies refactoring, and helps new contributors get productive faster.

The focus is on long-term quality and shared understanding, rather than short-term convenience.

---

## General Guidelines

As a general rule, prefer:

* Explicit code over implicit behavior
* Simple solutions over clever ones
* Predictable patterns over highly flexible abstractions

These choices tend to age better as the system grows.

---

## Functions

Well-structured functions typically:

* Have a single, clear responsibility
* Are easy to test
* Are small enough to understand at a glance

When a function starts doing too much, splitting it usually makes future changes safer and clearer.

---

## Naming

Good naming helps the code explain itself.

Names should clearly communicate intent and reduce the need for comments or additional context.

Example:

Less clear:

```python
def process(x):
```

More explicit:

```python
def evaluate_ocr_confidence(confidence_score):
```

---

## Error Handling

Error handling should aim to make failures visible and understandable.

Good practices include:

* Raising clear, explicit exceptions
* Providing enough context to diagnose issues

This improves debuggability and operational confidence.

---

## Domain-Specific Guidance

Domain code works best when it:

* Is deterministic and side-effect free
* Avoids framework or infrastructure dependencies
* Focuses purely on business rules

This keeps core logic stable and easy to refactor over time.

---

## LLM Usage

LLMs can be powerful productivity tools when used carefully.

To keep standards high:

* Review generated output thoughtfully
* Validate structured responses
* Treat prompts and generated logic with the same care as handwritten code

This approach helps ensure LLMs improve velocity without compromising maintainability.
