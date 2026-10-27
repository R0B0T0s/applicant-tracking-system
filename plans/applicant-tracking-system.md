# Plan: Applicant Tracking System

> Source PRD: `prd/applicant-tracking-system.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **Owning app**: One Django project with a `config` configuration package and a single `hiring` app that holds all domain models, views, forms, and templates.
- **URLs**: All app URLs are namespaced under `hiring:` and identify objects by integer pk (no slugs).
  - `/candidates/`, `/candidates/new/`, `/candidates/<pk>/`, `/candidates/<pk>/edit/`, `/candidates/<pk>/archive/`, `/candidates/<pk>/unarchive/`
  - `/jobs/`, `/jobs/new/`, `/jobs/<pk>/`, `/jobs/<pk>/edit/`, `/jobs/<pk>/close/`, `/jobs/<pk>/reopen/`, `/jobs/<pk>/board/`
  - `/skills/` (plus add/edit/delete under it)
  - Application creation is reachable from both `/candidates/<pk>/` and `/jobs/<pk>/`. Stage moves are POSTs to an application-scoped endpoint (`/applications/<pk>/move/`).
  - Login and logout use Django's built-in auth views at `/accounts/`, and the admin is at `/admin/`.
- **Models**:
  - `Candidate`: email is unique and stored lowercase. Source is a fixed choice plus optional details. Also `is_archived` and `archived_at`.
  - `JobOpening`: `hiring_manager` is an FK to User (PROTECT, limited to the Hiring Manager group). `status` is a choice field (Open/Closed). Also `closed_at` and an M2M to `Skill`.
  - `Skill`: name is trimmed and unique regardless of case.
  - `Application`: FK to Candidate (PROTECT) and FK to JobOpening. Unique on (candidate, job opening). Has a stage choice field with the eight stages, and `applied_at`.
  - `StageChange`: FK to Application, `from_stage` (nullable), `to_stage`, `changed_by` (User), `changed_at`.
- **Auth/roles**: Django's built-in auth, with login required on every app view. "Hiring Manager" is a Django Group created by a data migration. One shared helper/mixin decides whether a user is a manager, and manager-only views return 403. `is_staff` controls only admin access.
- **Stage rules**: A standalone rules module inside `hiring` is pure logic and covers both move validation and the allowed-moves list. Every stage change goes through a single "move to stage" operation on Application (target stage + acting user), which runs in one transaction and writes a StageChange.
- **Frontend**: Tailwind CSS + DaisyUI via django-tailwind-cli. HTMX handles partial updates on the board.
- **Tooling**: uv, Ruff, pytest + pytest-django, with tests organized by topic.

---

## Phase 1: Project skeleton and access control

**User stories**: 1, 2, 3, 4, 5, 6

### What to build

Set up the Django project (`config` + `hiring`) with uv, Ruff, pytest-django, Tailwind/DaisyUI, and HTMX. Add a base layout with navigation and a minimal home page. Login and logout use Django auth, and every app page redirects anonymous users to login. A data migration creates the "Hiring Manager" group. Add the shared is-manager helper/mixin and a friendly 403 page. To check it by hand: a superuser creates users in the admin, adds one to the group, and logs in as each.

### Acceptance criteria

- [ ] `uv run` starts the dev server, and Tailwind/DaisyUI styles render.
- [ ] Anonymous requests to app pages redirect to the login page.
- [ ] The "Hiring Manager" group exists after `migrate` on a fresh database.
- [ ] The is-manager helper returns true only for group members, not for `is_staff` users who aren't in the group.
- [ ] A manager-only test view (or the first real one) returns 403 to regular staff and shows a clear message.
- [ ] The pytest suite runs and passes, with tests for redirect-to-login and group existence.

---

## Phase 2: Candidates: create, list, search, detail, edit

**User stories**: 7, 8, 9, 10, 11

### What to build

The Candidate model, plus pages for list (with search), create, detail, and edit. Source is a fixed choice with optional source details. Email is normalized to lowercase and must be unique regardless of case, and the form shows a clear error for duplicates. Register the model in the admin.

### Acceptance criteria

- [ ] Staff can create a candidate with required and optional fields, and then see it on the detail page.
- [ ] Creating a candidate with an existing email in different capitalization is refused with a form error.
- [ ] Email is stored lowercase.
- [ ] Staff can edit a candidate.
- [ ] Searching the list matches name and email.
- [ ] Tests cover case-insensitive email uniqueness and login-required on all candidate pages.

---

## Phase 3: Candidate archiving

**User stories**: 13, 15, 16, 18

### What to build

Managers get archive and un-archive actions on the candidate detail page (POST, with a confirmation step). Archiving sets `is_archived` and `archived_at`, and un-archiving clears them. The candidate list hides archived candidates by default and offers a "show archived" filter. The app has no delete action. Admin deletion is limited to superusers, and PROTECT on Application blocks it once applications exist (verified in Phase 6).

### Acceptance criteria

- [ ] A manager can archive and un-archive a candidate, and the detail page shows the archived state.
- [ ] Regular staff get a 403 on archive and un-archive.
- [ ] Archived candidates are hidden from the list by default and appear with "show archived".
- [ ] The app UI has no candidate delete action.
- [ ] Tests cover permissions and the list filter.

---

## Phase 4: Job openings: create, list, search, detail, edit

**User stories**: 19, 20, 21, 22, 23, 30

### What to build

The JobOpening model (status defaults to Open), plus pages for list (with search), create, detail, and edit. The hiring manager dropdown lists only Hiring Manager group members and is required. The same rule is enforced in validation, not only in the choices. Salary min greater than max is rejected. Number of positions is a positive integer with a default of 1. Staff can't change status through the edit form. The PROTECT FK prevents deleting a user who is the hiring manager on any opening.

### Acceptance criteria

- [ ] Staff can create and edit a job opening with all fields.
- [ ] A salary min greater than max is rejected with a form error.
- [ ] The hiring manager dropdown contains only group members, and submitting a non-member (by tampering) is rejected.
- [ ] The edit form has no status field.
- [ ] Deleting a user who is the hiring manager on any opening fails.
- [ ] Searching the list matches title, department, and location.
- [ ] Tests cover salary validation, hiring manager limits, and delete protection.

---

## Phase 5: Skills

**User stories**: 31, 32, 33, 34

### What to build

The Skill model and a manager-only Skills page to list, add, rename, and delete skills. Names are trimmed, and uniqueness ignores case, enforced at the database level. The job opening form gets a multi-select of existing skills, and the job detail page shows them. One skill can be used on many openings.

### Acceptance criteria

- [ ] A manager can add, rename, and delete skills.
- [ ] Regular staff get a 403 on the Skills pages.
- [ ] Adding " python " when "Python" exists is refused.
- [ ] Staff can attach several skills to a job opening, and the job detail page shows them.
- [ ] The same skill can be attached to multiple openings.
- [ ] Tests cover duplicate names (case and whitespace) and permissions.

---

## Phase 6: Applications

**User stories**: 14, 17, 35, 36, 37, 38, 39

### What to build

The Application and StageChange models. Staff can record an application from the candidate page (choosing an open job) or from the job page (choosing a non-archived candidate). Each new application starts in Applied and writes an initial StageChange (empty from-stage → Applied, by the acting user). Duplicate (candidate, job) pairs are refused at the database and form level. Archived candidates (and closed openings, once closing exists) are excluded from choices and refused in validation. Both detail pages list the related applications with their current stage. Archiving is now blocked while a candidate has any application in an active stage, with a message telling the manager to withdraw or reject first.

### Acceptance criteria

- [ ] An application can be created from both the candidate page and the job page.
- [ ] A new application is in Applied and has exactly one StageChange (→ Applied).
- [ ] A second application for the same candidate and job is refused.
- [ ] A candidate can apply to several different openings.
- [ ] Archived candidates are left out of the form, and submitting one by tampering is refused.
- [ ] The model layer refuses an application to a closed opening (testable by setting status directly).
- [ ] Archiving a candidate with an active application is refused with the instructional message.
- [ ] Deleting a candidate with applications fails in the admin.
- [ ] Tests cover uniqueness, lifecycle refusals, and initial history.

---

## Phase 7: Stage rules and the Kanban board

**User stories**: 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 52, 53

### What to build

The pure stage rules module, built test-first:
- From an active stage, an application can move forward any number of stages up to Offer, move to Hired only from Offer, move back exactly one stage, or move to Rejected or Withdrawn.
- No normal moves are allowed out of a final stage.

The rules also produce the list of allowed moves. The "move to stage" operation on Application validates the move, updates the stage, and writes a StageChange in one transaction.

The board page for each job opening (`/jobs/<pk>/board/`) shows one column per active stage plus a compact final-stages section. Each card shows the candidate and a dropdown of only the allowed moves. Changing the dropdown sends an HTMX POST to the move endpoint, which re-checks the move on the server. It returns the updated board fragment on success, or the fragment with an inline error on the card when the move is rejected. Link the board from the job detail page.

### Acceptance criteria

- [ ] Rules tests: skipping forward up to Offer is allowed, Hired is allowed only from Offer, moving back is allowed one step only, Rejected and Withdrawn are reachable from every active stage, and final stages have no normal moves.
- [ ] Allowed-moves output matches the rules for every stage.
- [ ] Each successful move writes one StageChange with from, to, user, and time.
- [ ] The board shows applicants in the correct columns, with final stages in a separate compact section.
- [ ] Choosing a move updates the board without a full page reload.
- [ ] A tampered POST with an illegal target returns the fragment with an inline error, and the stage is unchanged.
- [ ] HTMX endpoint tests cover success, a blocked move, and dropdown contents.

---

## Phase 8: Manager reopen of final-stage applications

**User stories**: 50, 51

### What to build

A manager-only Reopen action, allowed only from Hired, Rejected, or Withdrawn. It returns the application to the from-stage of its most recent StageChange and records the reopen as a StageChange. It goes through the same rules and move operation, and appears as a "Reopen" option in the board dropdown on final-stage cards, for managers only. Reversing a hire is Hired → Reopen (to Offer) → Rejected.

### Acceptance criteria

- [ ] A manager can reopen a final-stage application, and it returns to the correct previous stage.
- [ ] Regular staff don't see Reopen, and a tampered reopen POST is refused.
- [ ] Reopen is refused for active-stage applications.
- [ ] Each reopen writes a StageChange.
- [ ] Hired → Reopen → Rejected works and shows in the history.
- [ ] Tests cover manager-only access and the correct return stage.

---

## Phase 9: Stage history timelines

**User stories**: 12, 54

### What to build

A timeline view of each application's StageChange history, showing from → to, who, and when, in chronological order. Corrections and reopenings appear as ordinary entries. The candidate detail page shows all of the candidate's applications with their timelines. The timeline is also reachable from the job opening's side, from the board card or the job detail application list.

### Acceptance criteria

- [ ] The candidate detail page shows every application with its full stage timeline.
- [ ] Timeline entries show the previous stage, new stage, user, and timestamp, with the initial "→ Applied" entry first.
- [ ] Reopenings and back-steps appear correctly.
- [ ] The timeline is reachable from the job opening side.

---

## Phase 10: Close and reopen job openings

**User stories**: 24, 25, 26, 27, 28, 29

### What to build

Manager-only close and reopen actions on job openings, each with a confirmation page. Closing sets the status to Closed and records `closed_at`. The confirmation warns how many active applications remain. Reopening sets the status back to Open and clears `closed_at`, and is allowed at any time. Closing changes no applications, and their stages can still be moved, including to Hired. Closed openings are excluded from the application form on the candidate page, and the job page hides or refuses "add application". The board and job detail page clearly show a "Closed" marker. The job page shows "X of N positions filled", where X is the count of Hired applications.

### Acceptance criteria

- [ ] A manager can close an opening, and the confirmation shows the active application count.
- [ ] A manager can reopen a closed opening, which clears `closed_at`.
- [ ] Regular staff get a 403 on close and reopen.
- [ ] Closed openings don't appear in the candidate-page application form, and creating an application for one is refused.
- [ ] Applications on a closed opening can still be moved, including to Hired.
- [ ] The board and detail page show a "Closed" marker.
- [ ] "X of N positions filled" is accurate.
- [ ] Tests cover lifecycle, permissions, and movement on closed openings.
