# Architecture

## Purpose

This document describes the architectural guidelines used across all agent microservices and explains **why they exist**. Following these guidelines helps ensure consistent code quality, easier refactoring, and lower maintenance cost as the system evolves.

The intent is not to be restrictive, but to provide a shared structure that scales well with more agents, contributors, and changing requirements.

---

## Canonical Agent Structure

All agents follow the same high-level structure. While individual agents differ in behavior, a consistent shape makes the system easier to understand, test, and extend.

The architecture is deliberately layered, with the **domain as the center of gravity**, so that business rules remain stable even as tooling, workflows, or vendors change.

---

## Layering Principles

Dependencies are designed to flow **inward**, toward the domain:

API → Services → Domain ← Repositories / Adapters

Workflows focus on orchestration and sequencing, while business logic and integrations live elsewhere. This separation helps keep changes localized and refactors safer.

---

## Layer Responsibilities

### api/

Acts as the entry point to the system.

Typically responsible for:

* Defining HTTP routes
* Binding requests and responses
* Triggering a service or workflow

Keeping this layer lightweight helps prevent business logic from leaking into the API surface.

---

### core/

Provides shared infrastructure used by all agents.

Common responsibilities include:

* Configuration loading
* Logging and telemetry setup
* Security hooks
* Base exception definitions

Centralizing these concerns avoids duplication and keeps agent-specific logic focused.

---

### domain/ (Business Rules)

Represents the core business logic of the agent.

This layer defines:

* Domain entities and value objects
* Business rules and invariants
* Valid vs. invalid states

By keeping the domain pure and independent, rules remain reusable, testable, and easy to reason about over time.

---

### models/

Defines data contracts at system boundaries.

These models describe request, response, and event shapes, helping ensure consistency and clarity when data enters or leaves the system.

---

### services/

Coordinates work across the system.

Services typically:

* Call adapters
* Invoke domain rules
* Prepare inputs for workflows

This layer allows execution details to change without impacting core business rules.

---

### adapters/

Encapsulate interactions with external systems.

Each adapter focuses on a single integration, which makes vendor changes or replacements easier and limits their impact on the rest of the codebase.

---

### workflows/

Defines control flow using LangGraph.

Workflows handle sequencing, retries, branching, and escalation, allowing execution paths to evolve independently from business logic and integrations.

---

### repositories/

Handles persistence concerns.

By isolating storage logic, the system can adapt to schema or database changes without affecting domain rules or services.

---

### utils/

Contains small, reusable helper functions.

These utilities are intentionally simple and stateless to avoid hidden dependencies or side effects.

---

## Why This Structure Helps

Using a consistent, layered architecture:

* Makes refactoring safer
* Improves testability
* Reduces coupling between components
* Helps new contributors ramp up faster

Following these guidelines supports good engineering standards and keeps the system maintainable in the long run.
