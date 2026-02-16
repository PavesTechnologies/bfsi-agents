# Front-End Guidelines
## Project: Intake Processing & Verification Platform
## Version: 1.0
## Status: Draft (Implementation-Ready)

---

## 1. Purpose

This document defines standards, conventions, and best practices for building the front-end interfaces of the Intake Processing & Verification Platform.

Goals:
- Ensure consistency
- Enable scalability
- Support compliance workflows
- Improve developer velocity
- Reduce UI defects
- Support audit and HITL use cases

---

## 2. Design Principles

### 2.1 Core Principles

| Principle | Description |
|-----------|-------------|
| Clarity | Information must be unambiguous |
| Consistency | Same behavior everywhere |
| Traceability | Every UI action traceable |
| Determinism | Same input = same output |
| Accessibility | WCAG-compliant |
| Security | No sensitive leakage |

---

### 2.2 UX Priorities

1. Status visibility
2. Error transparency
3. Evidence traceability
4. Review efficiency
5. Minimal cognitive load

---

## 3. Technology Stack

### 3.1 Mandatory

| Layer | Technology |
|-------|------------|
| Framework | React (Next.js preferred) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| State | React Query / Zustand |
| Forms | React Hook Form |
| Validation | Zod |
| Tables | TanStack Table |
| Charts | Recharts |
| Auth | JWT / OAuth Client |

---

### 3.2 Prohibited

- Plain JavaScript
- Inline styles
- jQuery
- Direct DOM manipulation
- Client-side secrets

---

## 4. Application Structure

### 4.1 Folder Structure

```
src/
 ├── app/
 ├── components/
 │    ├── common/
 │    ├── forms/
 │    ├── tables/
 │    └── layout/
 ├── features/
 │    ├── intake/
 │    ├── audit/
 │    ├── review/
 │    └── admin/
 ├── hooks/
 ├── services/
 ├── store/
 ├── styles/
 └── utils/
```

---

### 4.2 Feature-Based Organization

Each feature must contain:

```
feature/
 ├── api.ts
 ├── components/
 ├── hooks.ts
 ├── schema.ts
 ├── types.ts
 └── pages.tsx
```

No cross-feature imports.

---

## 5. UI Layout Standards

### 5.1 Global Layout

Required layout areas:

```
------------------------------------------------
 Header (Auth, User, System Status)
------------------------------------------------
 Sidebar (Navigation)
------------------------------------------------
 Main Content Area
------------------------------------------------
 Footer (Version, Audit Info)
------------------------------------------------
```

---

### 5.2 Responsive Breakpoints

| Size | Width |
|------|--------|
| Mobile | <640px |
| Tablet | 640–1024px |
| Desktop | >1024px |

Mobile-first design required.

---

## 6. Design System

### 6.1 Colors

| Purpose | Color |
|---------|--------|
| Primary | Blue/Indigo |
| Success | Green |
| Warning | Amber |
| Error | Red |
| Info | Gray |

No custom colors without approval.

---

### 6.2 Typography

| Type | Usage |
|------|-------|
| H1 | Page Title |
| H2 | Section |
| H3 | Subsection |
| Body | Content |
| Mono | IDs, Hashes |

---

### 6.3 Spacing

Use Tailwind spacing scale only.

Examples:
- p-2, p-4, p-6
- gap-2, gap-4

No arbitrary pixel values.

---

## 7. Navigation Guidelines

### 7.1 Primary Sections

| Section | Purpose |
|---------|----------|
| Dashboard | System overview |
| Intake | Requests |
| Review | HITL |
| Audit | Logs |
| Reports | Analytics |
| Admin | Config |

---

### 7.2 Routing Rules

- All routes versioned
- Lazy load features
- Guard protected routes
- No hardcoded URLs

---

## 8. State Management

### 8.1 Server State

Use React Query for:
- Fetching
- Caching
- Refetching
- Pagination

No custom fetch wrappers.

---

### 8.2 Client State

Use Zustand for:
- UI state
- Filters
- Preferences
- Session cache

No Redux unless approved.

---

## 9. API Integration

### 9.1 Service Layer

All API calls must go through:

```
/services/api-client.ts
```

Pattern:

```ts
service → hook → component
```

Direct fetch in components is forbidden.

---

### 9.2 Error Handling

Every API call must:

- Handle 4xx
- Handle 5xx
- Handle timeouts
- Handle retries

No silent failures.

---

## 10. Forms & Validation

### 10.1 Form Rules

- React Hook Form only
- Zod schemas mandatory
- No uncontrolled inputs
- No manual validation

---

### 10.2 Validation Behavior

| Type | Handling |
|------|----------|
| Client | Instant |
| Server | Displayed |
| Business | Flagged |

Errors must show reason codes.

---

## 11. Tables & Lists

### 11.1 Table Standards

All tables must support:

- Pagination
- Sorting
- Filtering
- Column hide/show
- Export (CSV)

---

### 11.2 Required Columns (Intake)

| Column | Required |
|--------|----------|
| Request ID | Yes |
| Status | Yes |
| Score | Yes |
| Created | Yes |
| Actions | Yes |

---

## 12. Status & Feedback

### 12.1 Job Status Display

Use standardized states:

| State | Color |
|-------|-------|
| QUEUED | Gray |
| RUNNING | Blue |
| COMPLETED | Green |
| PARTIAL | Amber |
| FAILED | Red |

---

### 12.2 Loading Indicators

- Skeletons preferred
- Spinners only for small blocks
- No blocking loaders

---

## 13. HITL Review Interface

### 13.1 Required Panels

```
---------------------------------
 Request Summary
---------------------------------
 Extracted Data
---------------------------------
 Evidence Viewer
---------------------------------
 Validation Errors
---------------------------------
 Actions
---------------------------------
```

---

### 13.2 Reviewer Actions

- Approve
- Reject
- Request Reprocess
- Escalate

All actions must be logged.

---

## 14. Audit & Evidence UI

### 14.1 Audit Viewer

Must support:

- Timeline view
- Diff view
- Filter by stage
- Hash verification

---

### 14.2 Evidence Viewer

Must display:

- Original document
- OCR overlay
- Bounding boxes
- Highlighted fields

Read-only mode enforced.

---

## 15. Security Guidelines

### 15.1 Data Handling

- Never store PII in localStorage
- Never log PII
- Mask sensitive fields
- Disable autocomplete on sensitive inputs

---

### 15.2 Authentication

- Token rotation
- Secure cookies
- Auto logout
- Inactivity timeout

---

## 16. Performance Guidelines

### 16.1 Targets

| Metric | Target |
|--------|--------|
| TTI | < 2s |
| LCP | < 2.5s |
| Bundle | < 300KB |

---

### 16.2 Optimization

- Code splitting
- Tree shaking
- Memoization
- Virtualized lists
- Image lazy loading

---

## 17. Accessibility (A11Y)

### 17.1 Standards

- WCAG 2.1 AA
- ARIA labels
- Keyboard navigation
- Screen reader support

---

### 17.2 Mandatory Checks

- Tab order
- Contrast
- Focus state
- Alt text

---

## 18. Logging & Telemetry

### 18.1 Client Logs

Must capture:

- Navigation
- Errors
- API failures
- Review actions

No sensitive data.

---

### 18.2 Tracing

All major actions must include:

- request_id
- user_id
- session_id

---

## 19. Testing Standards

### 19.1 Required Tests

| Type | Tool |
|------|------|
| Unit | Vitest |
| Integration | Testing Library |
| E2E | Playwright |
| A11Y | Axe |

---

### 19.2 Coverage

- Business logic: ≥90%
- Components: ≥80%
- Critical flows: 100%

---

## 20. CI/CD Rules

### 20.1 Build Pipeline

Must include:

- Lint
- Type check
- Test
- Build
- Bundle analysis

No bypass.

---

### 20.2 Release Gates

Blocked if:

- Tests fail
- Coverage drops
- Bundle > limit
- A11Y violations

---

## 21. Documentation

Each feature must include:

- README.md
- API contract
- UI screenshots
- State diagram

No undocumented features allowed.

---

## 22. Code Review Standards

All PRs must:

- Pass CI
- Include tests
- Include screenshots
- Reference ticket
- Have 2 approvals

No direct main commits.

---

## 23. Anti-Patterns (Strictly Forbidden)

- Business logic in components
- God components
- Prop drilling > 3 levels
- Hardcoded enums
- Inline API calls
- Copy-paste UI

---

## 24. Exit Criteria

Front-end is production-ready when:

- All pages responsive
- All states visible
- All errors actionable
- All flows tested
- All audits traceable
- All security rules enforced

---

## 25. Open Issues

1. Admin UI permission model?
2. Real-time updates via WebSocket?
3. Offline review support?
4. Mobile app roadmap?

---
