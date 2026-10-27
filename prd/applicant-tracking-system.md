# PRD: Applicant Tracking System

## Problem Statement

The hiring department has no shared system for tracking hiring. Staff involved in hiring need one place to keep candidate information, publish and maintain job openings, record which candidates applied to which openings, and see where every applicant stands in the hiring process. Today it is hard to tell who is in which stage, who moved them there, or whether a candidate already applied for a given opening. Hiring decisions such as rejections and hires can be changed or lost without a trace. The department has also not decided how candidate records should be retired over time, or what should happen to in-progress applicants when a job opening closes.

## Solution

An internal Django web application, used only by logged-in employees (candidates never log in), that lets staff:

- Maintain one record per real candidate, including where the candidate came from.
- Create and edit job openings, including the skills each opening requires, and open or close them.
- Record applications, one per candidate per opening.
- See each opening's pipeline as a Kanban board and move applicants between stages from a dropdown, without reloading the page.
- Rely on clear, enforced rules for how applications move between stages, with every move recorded in a history.
- Leave sensitive actions (undoing final decisions, archiving candidates, closing and reopening openings, managing the skill list) to Hiring Managers.

## User Stories

### Access and roles

1. As an employee, I want to log in before using the system, so that candidate information is only visible to authorized staff.
2. As a logged-out visitor, I want to be redirected to the login page when I try to open any page, so that no hiring data is exposed.
3. As a system administrator, I want to create employee accounts in the Django admin, so that I control who has access without a public sign-up.
4. As a system administrator, I want to make someone a Hiring Manager by adding them to the "Hiring Manager" group, so that roles are managed in one place.
5. As a system administrator, I want the "Hiring Manager" group to exist automatically in every new database, so that I never have to set it up by hand.
6. As a staff member, I want to see a clear "not allowed" response when I try a manager-only action, so that I understand why it didn't work.

### Candidates

7. As a staff member, I want to add a candidate with first name, last name, email, and optional phone, LinkedIn/portfolio URL, location, and notes, so that I have their basic information in one place.
8. As a staff member, I want to record a candidate's source (Website, Job Board, Referral, or Other) and optional source details, such as who referred them or which job board, so that we know where candidates come from.
9. As a staff member, I want the system to refuse a new candidate whose email already exists (ignoring upper/lowercase), so that each real person has only one record.
10. As a staff member, I want to edit a candidate's information, so that their record stays accurate.
11. As a staff member, I want to search the candidate list, so that I can quickly find a person.
12. As a staff member, I want to see a candidate's applications and their stage histories on the candidate's page, so that I understand their whole history with the company.
13. As a Hiring Manager, I want to archive a candidate, so that inactive candidates no longer clutter lists and pickers.
14. As a Hiring Manager, I want archiving to be blocked while the candidate has active applications, with a message telling me to withdraw or reject them first, so that no one is archived mid-process.
15. As a Hiring Manager, I want to un-archive a candidate, so that a returning candidate can be considered again.
16. As a staff member, I want archived candidates hidden by default, with a "show archived" option, so that lists focus on current candidates but history is still reachable.
17. As a staff member, I want archived candidates to be unable to receive new applications, so that inactive records stay inactive.
18. As a system administrator, I want hard deletion of candidates to be available only through the Django admin, and blocked for any candidate who has applications, so that hiring history is never destroyed by accident.

### Job openings

19. As a staff member, I want to create a job opening with title, department, location, employment type, description, optional salary range, hiring manager, and number of positions, so that the opening is fully described.
20. As a staff member, I want the system to reject a salary range whose minimum is greater than its maximum, so that the data stays sensible.
21. As a staff member, I want the hiring manager dropdown to list only members of the Hiring Manager group, and to require a choice, so that every opening has a valid owner.
22. As a staff member, I want to edit a job opening, so that I can correct or update its details.
23. As a staff member, I want to search the job list, so that I can quickly find an opening.
24. As a staff member, I want to see "X of N positions filled" on a job opening, so that I know how close we are to finishing hiring for it.
25. As a Hiring Manager, I want to close a job opening, so that it stops accepting new applications.
26. As a Hiring Manager, I want a warning when closing an opening that still has active applications, showing how many, so that I close it knowingly.
27. As a staff member, I want existing applications on a closed opening to keep moving through the stages, including to Hired, so that we can finish interviewing the people already in progress.
28. As a staff member, I want a closed opening to be clearly marked "Closed" on its board, so that I don't mistake it for an open one.
29. As a Hiring Manager, I want to reopen a closed job opening at any time, so that we can accept new applicants again without re-entering the job.
30. As a system administrator, I want a user who is the hiring manager on any opening to be protected from deletion, so that openings never lose their owner.

### Skills

31. As a Hiring Manager, I want to add, rename, and remove skills on a Skills page, so that the skill list stays clean and consistent.
32. As a Hiring Manager, I want duplicate skill names to be rejected regardless of capitalization or extra spaces, so that "Python" and " python " can't both exist.
33. As a staff member, I want to choose several skills for a job opening from the existing list, so that each opening shows the skills it needs.
34. As a staff member, I want the same skill to be usable across many job openings, so that skills are defined only once.

### Applications

35. As a staff member, I want to record that a candidate applied to an opening, starting from either the candidate's page or the job opening's page, so that I can enter it wherever I am working.
36. As a staff member, I want the system to refuse a second application from the same candidate to the same opening, so that there are no duplicate applications.
37. As a staff member, I want a candidate to be able to apply to several different openings, so that one person can be considered for many jobs.
38. As a staff member, I want closed openings and archived candidates left out of the application form, so that I can't create invalid applications.
39. As a staff member, I want every new application to start in the Applied stage, with that recorded in its history, so that the history is complete from day one.

### Pipeline board and stage moves

40. As a staff member, I want a Kanban board for each job opening with a column per stage, so that I can see at a glance where every applicant is.
41. As a staff member, I want the final stages (Hired, Rejected, Withdrawn) shown in a smaller, separate section, so that the board focuses on active applicants.
42. As a staff member, I want each applicant card to have a dropdown listing only the moves I'm allowed to make right now, so that I can't pick an illegal move.
43. As a staff member, I want choosing a stage from the dropdown to update the board without reloading the whole page, so that moving applicants is quick.
44. As a staff member, I want a clear error message on the card if a move is rejected, so that I know why it didn't happen.
45. As a staff member, I want to move an applicant forward several stages at once, up to Offer (for example, Applied straight to Interview for a strong referral), so that the system doesn't force pointless steps.
46. As a staff member, I want Hired to be reachable only from Offer, so that no one is marked hired without an offer on record.
47. As a staff member, I want to move an applicant back one stage at a time, so that I can fix mistakes, including a mistaken skip forward, by stepping back.
48. As a staff member, I want to move any active applicant (Applied through Offer) to Rejected or Withdrawn, so that I can end their process at any point.
49. As a staff member, I want Hired, Rejected, and Withdrawn to be final for me, so that hiring decisions can't be casually changed.
50. As a Hiring Manager, I want to reopen a Hired, Rejected, or Withdrawn application, returning it to the stage it was in before, so that mistakes and returning candidates can be handled.
51. As a Hiring Manager, I want to reverse a hire (for example, after a failed background check) by reopening it back to Offer and then rejecting it, so that the history shows exactly what happened.
52. As a staff member, I want the server to re-check every move against the rules, even if the request was tampered with, so that the rules can't be bypassed.

### History

53. As a staff member, I want every stage change recorded with the previous stage, new stage, who made it, and when, so that we can answer "who moved this candidate, and when?"
54. As a staff member, I want to see an application's stage history as a timeline, so that I can follow its path, including corrected mistakes and reopenings.

## Implementation Decisions

### Technology
- Python, Django, SQLite, uv for dependencies and running commands, Tailwind CSS with DaisyUI through django-tailwind-cli, HTMX for partial page updates, Ruff for linting and formatting.
- Automated tests use pytest with pytest-django.

### Project structure
- One Django project with a separate configuration package, and a single application (`hiring`) containing all domain models, views, forms, and templates.
- The stage transition rules live in their own module inside the `hiring` app, separate from views and models, so they can be tested in isolation.
- Tests are organized by topic (stage rules, candidates, job openings, applications, permissions, HTMX board).

### Authentication and roles
- Django's built-in authentication. Every app view requires login, and anonymous users are redirected to the login page.
- Accounts are created by a superuser in the Django admin. There is no sign-up or user-management UI in the app.
- Two roles: regular staff (any logged-in user) and Hiring Managers (members of a "Hiring Manager" Django Group). The `is_staff` flag is **not** used as the role flag; it only controls Django admin access.
- A data migration creates the "Hiring Manager" group.
- A small shared helper or mixin answers "is this user a Hiring Manager?" Manager-only views return 403 Forbidden to regular staff.
- Manager-only actions: archive and un-archive candidates, close and reopen job openings, reopen final-stage applications, and manage the skill list. Everything else is available to all logged-in staff.

### Models

**Candidate**
- First name, last name, email (required, unique, normalized to lowercase on save), phone (optional), LinkedIn/portfolio URL (optional), location (optional), notes (optional free text).
- Source: a fixed choice (Website, Job Board, Referral, Other) plus an optional free-text source details field. Source belongs to the candidate, not to each application.
- `is_archived` boolean and `archived_at` timestamp.

**JobOpening**
- Title, department, location, employment type (Full-time, Part-time, Contract, Internship), description.
- Salary minimum and maximum, both optional, validated so the minimum is not greater than the maximum.
- Hiring manager: a required foreign key to User, limited to members of the Hiring Manager group (both in form choices and in validation), with protect-on-delete.
- Number of positions: a positive integer, default 1. Information only; nothing is blocked or closed automatically.
- Status: a choice field (Open, Closed), chosen over a boolean so that statuses can be added later.
- `created_at`, and `closed_at` (set when closed, cleared when reopened).
- Many-to-many relationship to Skill.

**Skill**
- Name, unique and case-insensitive (trimmed of whitespace; uniqueness enforced regardless of letter case).
- Linked to job openings with a plain many-to-many relationship (no extra fields such as required/preferred).

**Application**
- Foreign key to Candidate (protect-on-delete), foreign key to JobOpening, current stage, `applied_at`.
- A database uniqueness constraint on (candidate, job opening).
- Stage is a choice field with the eight required stages: Applied, Screening, Interview, Final Review, Offer, Hired, Rejected, Withdrawn.
- New applications start in Applied. Creating one is refused if the job opening is closed or the candidate is archived.

**StageChange**
- Foreign key to Application, from-stage (empty for the first entry), to-stage, changed-by (User), changed-at.
- One row is written for every successful stage move, every reopen, and the initial "→ Applied" when an application is created.

### Stage transition rules
- Active stages: Applied, Screening, Interview, Final Review, Offer. Final stages: Hired, Rejected, Withdrawn.
- From an active stage:
  - Move forward any number of stages, up to and including Offer.
  - Hired is allowed only from Offer.
  - Move back exactly one stage.
  - Move to Rejected or Withdrawn.
- From a final stage, no normal moves are allowed by anyone.
- **Reopen** (Hiring Managers only) is allowed only from a final stage. It returns the application to the from-stage of its most recent stage change, and is itself recorded as a stage change.
- There is no "undo last move" action. A mistaken skip forward is corrected by stepping back one stage at a time.
- All rule checks go through a single entry point on the application (a "move to stage" operation that takes the target stage and the acting user). It validates the move, updates the stage, and writes the StageChange inside one transaction. Views stay thin and call this operation.
- The same rules produce the list of allowed moves for a given application and user, which drives the board dropdowns.
- Stage moves are allowed on applications to closed job openings.

### Candidate lifecycle
- Any staff member can edit candidates.
- Hiring Managers can archive and un-archive. Archiving is refused while the candidate has any application in an active stage.
- Archived candidates are excluded from candidate lists by default (a "show archived" filter includes them) and from the application form.
- The app has no delete action for candidates. Deletion is possible only in the Django admin by a superuser, and is blocked at the database level for candidates who have applications.

### Job opening lifecycle
- Any staff member can create and edit job openings, except for changing status.
- Only Hiring Managers can close or reopen. Closing sets status to Closed and records `closed_at`. Reopening sets status to Open and clears `closed_at`. Reopening is allowed at any time, with no position or time limits.
- Closing does not change any applications. It only stops new applications. The close confirmation shows how many active applications remain.
- The job page shows "X of N positions filled," where X is the number of applications in Hired.

### Pages and interactions
- Candidate list (search, show-archived filter), candidate detail (info, applications, stage histories, manager archive controls), candidate create/edit.
- Job opening list (search), job opening detail, job opening create/edit (including skill multi-select), close/reopen confirmation (manager only).
- Skills page for managers (list, add, edit, delete).
- Application creation from the candidate page (choose an open job) and from the job page (choose a non-archived candidate).
- Per-job Kanban board: one column per active stage, plus a compact section for final stages. Each card shows the candidate and a stage dropdown with only the currently allowed moves (including Reopen for managers on final-stage cards).
- Changing a card's dropdown sends an HTMX POST. The server runs the move operation and returns the updated board fragment on success, or the fragment with an inline error on failure, without a full page reload.
- Application stage history is shown as a timeline.
- Styling uses Tailwind CSS and DaisyUI components.

### Testing
- pytest + pytest-django. Required coverage:
  1. Stage rules: skip forward up to Offer, Hired only from Offer, back one step only, exits from any active stage, final stages blocked, Reopen manager-only and returning to the correct stage, a StageChange written for each move and for creation, and allowed-moves output matching the rules.
  2. Uniqueness: duplicate candidate email (case-insensitive), duplicate application for the same opening, duplicate skill name (case and whitespace).
  3. Lifecycle: no new applications to closed openings or archived candidates, archiving blocked with active applications, close/reopen manager-only, applications on closed openings still movable.
  4. Permissions: anonymous users redirected to login, staff get 403 on manager-only actions.
  5. HTMX board endpoint: success returns the updated board, a blocked move returns an error, and the dropdown lists only allowed moves.

## Out of Scope

- Candidate login, a candidate portal, or a public job board.
- In-app user management (invitations, role assignment screens); handled in the Django admin.
- Finer-grained roles (Recruiter, Interviewer, HR Admin) and per-job ownership permissions; the hiring manager field is a label only.
- Resume or file uploads, work history, education.
- Skills on candidates and candidate-to-job skill matching; required vs. preferred skills.
- Source tracked per application, and an editable list of sources.
- Additional job statuses (Draft, On Hold, Filled), automatic closing when positions are filled, blocking hires beyond the number of positions, and time-limited reopening.
- Bulk actions when closing an opening (such as auto-rejecting all active applications) or archiving a candidate (such as auto-withdrawing).
- An "undo last move" action, and moving back more than one stage at a time.
- Notes or reasons attached to stage changes; open/close history for job openings.
- Drag-and-drop on the Kanban board.
- An all-applications table across every opening (a possible later addition).
- Email notifications, scheduling interviews, reporting dashboards.
- Hard-deleting candidates from within the app.

## Further Notes

- The stage rules were checked with an interactive prototype (`prototypes/stage-transitions.html`). Its rule set C was chosen, then refined so that Hired is reachable only from Offer. The prototype is throwaway and must not be promoted into production code.
- The stage rule module and the "move to stage" operation are the most important pieces to build test-first; they are pure logic and drive the board, permissions, and history.
- Open business decisions from the original requirements (8: candidate record lifecycle; 9: job closing and reopening) are resolved as described above under "Candidate lifecycle" and "Job opening lifecycle."
