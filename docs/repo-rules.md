# Repository Rules

## Branching Strategy

* main is always deployable
* No direct commits to main
* Feature branches only

---

## Commits

Commits must explain:

* What changed
* Why it changed

Bad:

```
fix bug
```

Good:

```
remove domain dependency from service layer
```

---

## Pull Requests

PRs are reviewed for:

* Architectural compliance
* Layer violations
* Long-term maintainability

Passing tests does not override architectural violations.

---

## Repository Hygiene

* No dumping grounds (misc/, helpers/)
* If you can’t name it, you don’t understand it
* Delete dead code aggressively

---

## Documentation

* Architecture docs are mandatory
* If behavior changes, docs change

Undocumented behavior is a bug.
