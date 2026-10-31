# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-10-30 — Implemented Phase 7 (stage rules and the Kanban board)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Implement Phase 7`
2. "go ahead" (the three TDD behaviors: allowed moves for every stage, `move_to_stage` records history and refuses illegal moves, and a tampered move POST returns the board with an inline error)
3. "Approved" (behavior 1 RED test)
4. "Move on"
5. "Approved" (behavior 2 RED test)
6. "Move on"
7. "Approved" (behavior 3 RED test)
8. "Go ahead"
9. "Everything works"

### Summary
- **Outcome:** Added `hiring/stages.py`, a pure rules module with no Django imports: stage constants, `ACTIVE_STAGES`, `FINAL_STAGES`, `allowed_moves(stage)` (forward any number up to Offer, Hired only from Offer, back exactly one, Rejected/Withdrawn from any active stage, nothing from a final stage), and `is_allowed()`. Added `Application.move_to_stage(stage, user)`, which checks the rules, then saves the stage and writes a StageChange in one transaction, raising `ValidationError` ("Can't move from X to Y.") otherwise. Added the board at `/jobs/<pk>/board/` with five active columns and a compact "Final stages" section, cards with a dropdown of only the allowed moves, and an HTMX POST to `/applications/<pk>/move/` that swaps the `#board` fragment and shows refused moves inline on the card. Added the HTMX CSRF header on `<body>` and a "Pipeline board" button on the job detail page. Three behaviors were built test-first (RED, then GREEN). Normal tests cover login-required, column placement, dropdown contents, final cards without a dropdown, the success fragment, GET refused on the move endpoint, the board link, moves on closed openings, and unknown stages. 90 tests pass, and Ruff is clean. Manually verified in the browser.
- **Deviations:**
  - The move endpoint returns 200 even for a refused move, because HTMX 2 doesn't swap 4xx responses by default and the inline error would never show.
  - Final-stage cards have no dropdown for anyone yet; manager Reopen is Phase 8.
  - Each test file keeps its own fixtures, following the existing pattern, instead of a shared `conftest.py`.
- **Sideways:**
  - At behavior 1's RED step, the three final-stage cases already passed because the stub returned `[]`; Claude called this out and kept them as guards.
  - For behavior 3 to fail on an assertion rather than a crash, the move view was first built to swallow the error, and passing it to the card was the GREEN step.
  - Ruff reformatted the two new test files; no behavior changed.
  - CLAUDE.md still had uncommitted edits from before this session; they were left out of the Phase 7 commit.

## 2026-10-30 — Implemented Phase 6 (applications)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Implement Phase 6`
2. "I approve" (the three TDD behaviors: a new application starts in Applied with one history entry, the model refuses closed openings and archived candidates, and archiving is blocked while a candidate has active applications)
3. "Approved" (behavior 1 RED test)
4. "Move on"
5. "Approved" (behavior 2 RED test)
6. "Move on"
7. "I approve" (behavior 3 RED test)
8. "Go ahead"
9. "Manual Verification has passed."

### Summary
- **Outcome:** Added the `Application` and `StageChange` models (migration `0005_application_stagechange`). `Application` has the eight stages, `ACTIVE_STAGES`, PROTECT FKs to Candidate and JobOpening, and a unique (candidate, job opening) constraint with a clear message. `Application.objects.create_application(candidate, job_opening, user)` validates, saves in Applied, and writes the first StageChange (empty → Applied, by the acting user) in one transaction. `Application.clean()` refuses new applications to closed openings or archived candidates. `Candidate.archive_blocked_reason()`, `archive()`, and `unarchive()` moved archiving into the model, and the archive confirm page shows the instruction and hides the button while active applications exist. Added `ApplicationForm`, which fixes one side and limits the other to open jobs or non-archived candidates, plus "Add application" (candidate page, `/candidates/<pk>/apply/`) and "Add applicant" (job page, `/jobs/<pk>/applications/new/`). Both detail pages now list applications with their stage. The admin shows applications read-only, with their history inline. Three behaviors were built test-first (RED, then GREEN). Normal tests cover login-required, creating from both pages, duplicates at the form and database level, several openings per candidate, archived and closed choices left out and refused on tampering, application lists on both pages, archiving allowed with only final-stage applications, and candidate delete protection in the admin and the database. 70 tests pass, and Ruff is clean. Manually verified in the browser.
- **Deviations:**
  - `StageChange.from_stage` stores an empty string for the first entry instead of NULL (the plan says nullable), because Ruff's `DJ001` rule forbids nullable CharFields. Claude flagged this at behavior 1's RED step, and I approved.
  - `Application.job_opening` is PROTECT, like `candidate`, although the PRD names PROTECT only for candidate.
  - The admin is read-only for applications so history can't be skipped or edited there.
  - Closing a job isn't in the UI until Phase 10, so the closed-opening rules were checked by tests only, not by hand.
- **Sideways:**
  - Django's ModelForm skips constraints on fields missing from the form, which would have skipped the duplicate check (each form shows only one of the two fields). Claude overrode `ApplicationForm.validate_constraints()` to check the whole instance.
  - The first admin delete test expected Django's "protected related objects" message, but the admin refused the delete because the read-only Application admin has no delete permission. Claude changed that test to check for "Cannot delete candidate" and added a separate test that the database raises `ProtectedError`.
  - Ruff reformatted `test_applications.py`; no behavior changed.
  - CLAUDE.md still had uncommitted edits from before this session; they were left out of the Phase 6 commit.

## 2026-10-30 — Implemented Phase 5 (skills)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Implement Phase 5`
2. "Approved" (the two TDD behaviors: trimmed, case-insensitive unique skill names at the database level, and a form error for " python " when "Python" exists)
3. "Approved" (behavior 1 RED test)
4. "yes, move on to behavior 2"
5. "Approved" (behavior 2 RED test)
6. "Continue with the rest of the phase"
7. "Everything looks great"

### Summary
- **Outcome:** Added the `Skill` model (migration `0004_skill`). `save()` trims the name, and a `UniqueConstraint(Lower("name"))` makes the database refuse duplicates in any letter case. `Skill.validate_constraints()` moves the constraint's error onto the `name` field so forms show it under the input. Added manager-only Skills pages at `/skills/` (list with a count of openings per skill, add, rename, and delete with a confirmation page that says how many openings use the skill). Added a `skills` many-to-many on `JobOpening` (`related_name="job_openings"`), a checkbox multi-select on the job form, skill badges on the job detail page, a managers-only "Skills" nav link, a "Manage skills" button on Manager tools, and admin registration. Two behaviors were built test-first (RED, then GREEN). Normal tests cover login-required, staff 403 on every Skills page (GET and POST), the managers-only nav link, add/rename/delete, rename duplicate checks (a case-only change to the same skill is allowed), a blank name, several skills on one opening shown on the detail page, optional and editable job skills, one skill on several openings, and deleting a skill that is in use. 53 tests pass, and Ruff is clean. Manually verified in the browser.
- **Deviations:**
  - Claude proposed two TDD behaviors instead of three. The 403s reuse the tested `@hiring_manager_required` decorator, and the job-form multi-select uses the settled ModelForm pattern, so both got normal tests.
  - Behavior 2 changed meaning at RED: the duplicate was already refused, but the error showed at the top of the form instead of on the Name field. Claude pointed out that the top-of-form error arguably met the acceptance criterion; I approved the test that requires the error on the field.
- **Sideways:**
  - When proposing behavior 2, Claude predicted the form would miss the duplicate and crash on save, as email did in Phase 2. That was wrong: Django's form field trims spaces and the form checks the database constraint before saving. Claude corrected the claim when showing the RED result.
  - The `0004_skill` migration was regenerated twice (after adding the constraint, then after adding the `JobOpening.skills` field). It was never committed or applied.
  - The `JobOpening.skills` field was added during behavior 2's scaffolding, because the Skills list counts openings per skill.
  - Ruff reformatted `test_skills.py`; no behavior changed.
  - CLAUDE.md had uncommitted edits from before this session; they were left out of the Phase 5 commit.

## 2026-10-30 — Implemented Phase 4 (job openings: create, list, search, detail, edit)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Implement Phase 4`
2. "I approve" (the two TDD behaviors: salary min > max rejected, and hiring manager limited to Hiring Manager group members)
3. "I approve" (behavior 1 RED test, salary validation)
4. "Move on"
5. "I approve" (behavior 2 RED test, hiring manager limits)
6. "Move on"
7. "Move on" (remaining non-TDD requirements and feedback loops)
8. "Everything works as intended"

### Summary
- **Outcome:** Added the `JobOpening` model (migration `0003_jobopening`) with title, department, location, employment type, description, optional salary min/max, hiring manager, number of positions (default 1, minimum 1), status (default Open), `created_at`, and `closed_at`. `JobOpening.clean()` rejects a salary min greater than the max, with the error on `salary_min`. The `hiring_manager` FK uses `limit_choices_to` on the Hiring Manager group, which filters the dropdown and re-checks tampered POSTs in validation, and `PROTECT` blocks deleting a user who manages an opening. Added list (search by title, department, location), create, detail, and edit pages; the form has no status field. Added "Job openings" to the navbar and home page, and registered the model in the admin. Two behaviors were built test-first (RED, then GREEN). Normal tests cover login-required, page rendering, create and edit, required fields, positions default and minimum, no status field (including a tampered status POST), delete protection, and search. 41 tests pass, and Ruff is clean. Manually verified in the browser.
- **Deviations:**
  - Claude proposed two TDD behaviors instead of three. Delete protection, search, and the missing status field got normal tests because they are one-line declarations or reuse the tested candidate search pattern.
  - Claude asked whether the salary error should sit on the min field or at the top of the form; I approved the test as written (min field).
- **Sideways:**
  - A long shell command that wrote several files with nested heredocs failed to parse (`unexpected EOF while looking for matching '`). Nothing was changed. Claude confirmed with `git status` and rewrote the files with the editor tools instead.
  - A `cd` in an earlier shell command moved the session into `hiring/tests/`. Later commands used absolute paths, so nothing broke.
  - The `0003_jobopening` migration was generated before the hiring-manager restriction existed. Since it was never committed or applied, Claude deleted and regenerated it.
  - Ruff flagged `get_absolute_url` coming after `clean()` (DJ012). Claude reordered the methods.
  - Salaries were shown as "$90000" at first. Claude switched to `floatformat:"0g"` ("$90,000") before manual verification and updated the test.
  - CLAUDE.md had uncommitted edits from before this session; they were left out of the Phase 4 commit.

## 2026-10-30 — Implemented Phase 3 (candidate archiving)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Implement Phase 3`
2. "Approved" (the two TDD behaviors: manager archive/un-archive, and the list hiding archived candidates unless "show archived" is on)
3. "I approve" (behavior 1 RED test)
4. "yes, move on to behavior 2"
5. "I approve" (behavior 2 RED test)
6. "Continue with the rest of the phase"
7. "Everything works"

### Summary
- **Outcome:** Added manager-only `candidate_archive` and `candidate_unarchive` views at `/candidates/<pk>/archive/` and `/unarchive/`. A GET shows a confirmation page, and a POST sets or clears `is_archived` and `archived_at`. The candidate detail page shows an "Archived" badge, the archive date, and Archive or Un-archive buttons for managers only. The candidate list hides archived candidates by default, and a "Show archived" checkbox (which works with search) shows them with a badge. The admin allows candidate deletion only for superusers. Two behaviors were built test-first (RED, then GREEN). Normal tests cover login-required, staff 403 on GET and POST, the confirmation step not archiving, manager-only controls, the archived state on the detail page, no delete action in the app, and superuser-only admin delete. 27 tests pass, and Ruff is clean. Manually verified in the browser.
- **Deviations:**
  - Claude proposed two TDD behaviors instead of three. The staff 403 was left to a normal test because it reuses the already-tested `@hiring_manager_required` decorator.
  - Blocking archive while a candidate has active applications (story 14) isn't in this phase; the plan puts it in Phase 6, once applications exist.
- **Sideways:**
  - Behavior 1's first run failed with `NoReverseMatch`, not an assertion. Claude treated that as missing scaffolding, added the URLs and stub views, and reran to get a real RED (`assert False is True`).
  - To confirm the admin-delete test wasn't passing by accident, Claude temporarily replaced the superuser check with Django's default. The test failed, and the check was restored.
  - Ruff reformatted the test file after the new tests were appended; no behavior changed.

## 2026-10-29 — Implemented Phase 2 (candidates: create, list, search, detail, edit)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Implement phase 2`
2. "Approved" (the three TDD behaviors: lowercase email storage, case-insensitive duplicate email form error, search by name and email)
3. "approve" (behavior 2 RED test, lowercase storage)
4. "yes, move on"
5. "approved" (behavior 1 RED test, duplicate email)
6. "move on"
7. "Approved" (behavior 3 RED test, search)
8. "Continue with the rest of the phase"
9. "Everything works"

### Summary
- **Outcome:** Added the `Candidate` model (required and optional fields, a fixed source choice plus source details, and `is_archived`/`archived_at` for Phase 3), with email lowercased in `save()` and a unique constraint with a clear error message. Added `CandidateForm`, whose `clean_email` lowercases the email before Django's unique check. Added list (with search on first name, last name, and email), create, detail, and edit pages styled with DaisyUI 5, a "Candidates" nav link and home-page button, and admin registration with search and filters. Three behaviors were built test-first (RED, then GREEN). Normal tests cover login-required on all four candidate pages, page rendering, create and detail, required fields, editing, and editing into another candidate's email. 16 tests pass, and Ruff is clean. Manually verified in the browser.
- **Deviations:**
  - Built behavior 2 (lowercase storage) before behavior 1 (duplicate email), because the duplicate check depends on it.
  - Search matches each field on its own, so a full name like "Ada Lovelace" doesn't match. Claude flagged this as a possible follow-up; the plan asks only for matching on name and email.
- **Sideways:**
  - Behavior 1's first RED run crashed with an `IntegrityError` instead of failing an assertion. Claude explained that the crash was the bug itself (the form's exact-match unique check missed the duplicate, and the database's unique constraint then rejected the lowercased email), and set `client.raise_request_exception = False` so the test failed on `500 == 200` without changing its assertions.
  - Adding the custom unique error message produced a second migration. Since nothing was committed, Claude deleted and regenerated `0002_candidate` instead of keeping a `0003`.
  - A normal test exposed that `CandidateForm(request.POST or None)` treated a POST with no data as a GET, so it returned no errors. Both views now check `request.method`.
  - Claude checked the built CSS to confirm DaisyUI 5 before relying on its `fieldset` classes. The Phase 1 login page still uses DaisyUI 4's `form-control`, which is harmless and was left alone.

## 2026-10-29 — Wrote CLAUDE.md and implemented Phase 1 (project skeleton and access control)

### Prompts
1. "Create the initial CLAUDE.md for this project. Keep it between 20-30 lines long." (pasted rules: only a one-line description, the stack and package manager, durable PRD architecture decisions, and pointers to the PRD, plan, and prototypes; no commands, predicted structure, business rules, or invented conventions)
2. "In CLAUDE.md remove feature-specific business rules and anything that predicts commands or project structure. Keep only the project description, technology stack, document pointers, and durable architecture decisions from the PRD."
3. "commit CLAUDE.md to github"
4. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md Implement Phase 1`
5. "approved" (the three TDD behaviors: is-manager helper, anonymous redirect to login, manager-only 403)
6. "I approve" (behavior 1 RED test)
7. "yes, move on to behavior 2"
8. "Approved" (behavior 2 RED test)
9. "yes, move on to behavior 3"
10. "Approved" (behavior 3 RED test)
11. "Whenever I open http://127.0.0.1:8000/ I am met with a white screen."
12. "Everything works"

### Summary
- **Outcome:** Wrote and trimmed `CLAUDE.md` (stack, durable auth/role and stage-change architecture decisions, doc pointers) and pushed it. Built Phase 1: a uv project with Django 6.1, django-tailwind-cli with DaisyUI, HTMX from a pinned CDN, Ruff, and pytest-django. Added the `config` project and `hiring` app, `LoginRequiredMiddleware` for site-wide login, Django auth login/logout with a styled login page, a data migration that creates the "Hiring Manager" group, `is_hiring_manager` and a `hiring_manager_required` decorator in `hiring/permissions.py`, a friendly `403.html`, a home page, and a placeholder manager-only "Manager tools" page linked in the nav for managers. Three behaviors were built test-first (RED, then GREEN), plus a normal test for the group's existence; 4 tests pass, and Ruff is clean. Manually verified in the browser.
- **Deviations:**
  - CLAUDE.md first draft named the `hiring` app, stage-rule details, and the Hiring Manager group. I asked for a second pass that removed project structure and feature rules. Claude kept the stage-change transaction decision and flagged it as the closest call.
  - The shared role helper is a decorator, not a mixin, because the views are function-based (the PRD allows "helper or mixin").
  - The manager-only page is a placeholder test view, as the plan allows, since Phase 1 has no real manager feature.
- **Sideways:**
  - Claude reported CLAUDE.md as 24 lines; git showed 27. Corrected after the commit.
  - A PowerShell string replace on `settings.py` silently did nothing (CRLF line endings); redone with Edit.
  - `LoginRequiredMiddleware` was added before its test, so the RED step would not have failed. Claude removed it, showed RED, then added it back as the GREEN step.
  - Claude said logged-out visitors to `/admin/` would go to the app login page; the smoke test showed the admin keeps its own login. Corrected before manual verification.
  - Removing an unverified SRI hash from the HTMX `<script>` tag also deleted its closing `>`, which made every page render as a white screen in the browser. Tests passed because they only check status codes and text. I caught it during manual verification, and Claude fixed the tag.
  - While stopping its own test servers, Claude force-stopped all project `python` processes and all `uv` processes, which likely killed my running dev server. Claude disclosed it and I restarted the server.

## 2026-10-26 — Grilled the project idea, prototyped stage rules, wrote the PRD

### Prompts
1. `/grill-me @project-idea.md`
2. `b` (Q1 roles: two roles, Staff and Hiring Managers)
3. `a` (Q2 accounts: created in Django admin, "Hiring Manager" Group)
4. `b` (Q3 candidate fields: basic fields plus optional extras, unique email)
5. `b` (Q4 source: choice list plus details field, on Candidate)
6. `c` (Q5 job opening fields: adds salary range, hiring manager, number of positions)
7. `b` (Q6 hiring manager: required, Hiring Manager Group members only, label only)
8. `b` (Q7 number of positions: shows "X of N filled", no blocking)
9. `a` (Q8 skills: Skill model with plain many-to-many)
10. `/prototype` (asked while Q9, stage transition rules, was open)
11. "how would I check this in the browser?"
12. "Lets move forward with option C" (Q9: skip forward, back one step, final stages reopenable by managers)
13. `b` (Q10: Hired only from Offer)
14. `a` (Q11: fix mistaken skips by stepping back one stage at a time)
15. `b` (Q12: StageChange history model)
16. `a` (Q13: per-job Kanban board with HTMX dropdown of allowed moves)
17. `b` (Q14: archive and un-archive by managers, no in-app delete)
18. `c` (Q15: closing a job only stops new applications)
19. `b` (Q16: managers can reopen closed jobs at any time)
20. `a` (Q17: single `hiring` app)
21. `b` (Q18: pytest + pytest-django)
22. `/to-prd`
23. "Write this session log to PROMPTS.md according to its instructions."

### Summary
- **Outcome:** Resolved 18 design questions covering roles, models, stage rules, the Kanban UI, candidate and job lifecycles (business requirements 8 and 9), project structure, and testing. Built a throwaway interactive prototype, `prototypes/stage-transitions.html`, to compare stage-rule sets A–D, and chose rule set C. Wrote the PRD to `prd/applicant-tracking-system.md`. No Django code yet. The prototype, the PRD, and `project-idea.md` are uncommitted.
- **Deviations:**
  - Q5: chose C (richer job fields: salary, hiring manager, positions) over the recommended B.
  - Q8: chose A but didn't answer the follow-up about who manages skills. Claude assumed Hiring Managers manage the list and asked to be corrected if wrong.
  - Q9: instead of answering, I ran `/prototype` to test the rule sets, then asked how to open the prototype in a browser before choosing C.
  - Q10 and Q11 were follow-ups that came out of the prototype (the "Applied → Hired" and "mis-click forward" scenarios).
  - Q14: chose plain B. Claude carried over its recommended assumption that archiving is blocked while a candidate has active applications, and flagged it for correction.
  - Q18: the recommendation was conditional (pytest if the class covered it, otherwise Django's TestCase); I chose pytest.
  - All other answers matched the recommendation.
- **Sideways:**
  - The prototype's JavaScript passed a syntax check with Node, but Claude never opened it in a browser; I was given steps to check it myself.
  - A directory listing failed with exit code 2 because `prd/` didn't exist yet. This was harmless; the folder was created when the PRD was written.
  - A `cd` in a shell command moved the session's working directory into `prototypes/`. Later commands used absolute paths, so nothing broke.