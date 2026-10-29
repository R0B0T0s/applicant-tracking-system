# Applicant Tracking System

Internal Django web app where logged-in hiring staff track candidates, job openings, applications, and pipeline stages.

## Technology stack

- Python, Django, SQLite
- uv for dependency management
- Tailwind CSS + DaisyUI via django-tailwind-cli
- HTMX for partial page updates
- Ruff for linting and formatting
- pytest + pytest-django for tests

## Architecture decisions

- Authentication uses Django's built-in auth, and every app view requires login.
- There is no public sign-up. Accounts are created in the Django admin.
- Roles use Django Groups. `is_staff` controls admin access only and is never used as a role flag.
- Permission checks go through one shared helper/mixin, and unauthorized views return 403.
- Stage-transition logic is pure and kept separate from views and models.
- Every stage change goes through one model-level operation that validates the move and records history in a single transaction. Views stay thin.

## References

- PRD: `prd/applicant-tracking-system.md`
- Implementation plan: `plans/applicant-tracking-system.md`
- Prototypes: `prototypes/` (throwaway; never promote into production code)
