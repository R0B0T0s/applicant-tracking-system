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