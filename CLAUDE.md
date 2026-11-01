# Applicant Tracking System

Internal Django web application for the hiring department. Logged-in
employees keep one record per candidate, maintain job openings and the
skills they require, record which candidates applied to which openings, and
follow each application through a staged hiring pipeline with a full
history of every move.

Only employees use the system. Candidates never log in.

## Technology stack

- Python, Django, SQLite
- uv for dependencies and running commands
- Tailwind CSS + DaisyUI via django-tailwind-cli
- HTMX for partial page updates
- Ruff for linting and formatting
- pytest + pytest-django for tests

## Architecture decisions

### Access and roles

- Authentication uses Django's built-in auth. Every app view requires login,
  and anonymous users are redirected to the login page.
- There is no public sign-up and no in-app user management. Accounts and
  role membership are managed in the Django admin.
- Roles are Django Groups, and the role groups are created by data
  migration. `is_staff` controls admin access only and is never a role flag.
- Every role check goes through one shared helper. Views a user isn't
  allowed to use return 403 Forbidden.

### Domain logic

- Stage-transition rules are pure logic with no Django imports, kept
  separate from views and models so they can be tested in isolation.
- The same rules both validate a move and produce the list of moves allowed
  right now, so the UI only offers what the server will accept.
- Every stage change goes through one model-level operation that takes the
  target stage and the acting user. It validates the move, updates the
  stage, and records the history entry in a single transaction.
- Business rules are enforced in the model and database layer (validation,
  model methods, constraints), not only in form choices, so tampered
  requests are refused.
- Views stay thin and call model operations; they hold no business rules.
- Status-like fields are choice fields, not booleans, so values can be
  added later.

### Data integrity and history

- Stage history is append-only. Every change records the previous stage,
  the new stage, who made it, and when.
- Hiring records are retired, never destroyed. The app has no hard-delete
  for records with history, and protect-on-delete keys stop deletions in
  the admin from removing that history.

### Frontend

- Pages are server-rendered Django templates styled with Tailwind CSS and
  DaisyUI components.
- Interactive updates use HTMX. The server re-checks every request and
  returns the updated HTML fragment, with errors shown inline.

## References

- PRD: `prd/applicant-tracking-system.md`
- Implementation plan: `plans/applicant-tracking-system.md`
- Prototypes: `prototypes/` (throwaway; never promote into production code)
