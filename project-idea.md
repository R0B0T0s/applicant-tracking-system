This is a new Django application called Applicant Tracking System. 

Objectives: Able to manage job openings, track canidates, and move applications through the hiring process. 


Technology Requirements
Your project must use the following technology stack:

1. Python

2. Django

3. SQLite

4. uv

5. Tailwind CSS with DaisyUI using django-tailwind-cli

6. HTMX

7. Ruff

Your project must also include automated tests. You may use either Django's built-in testing framework or pytest.


Business Requirements
The hiring department has provided the following requirements.

1. This is an internal hiring system. It will be used by employees involved in the hiring process. Candidates will not log in to the system.

2. Staff need to keep track of candidates and their basic information. Candidates may come from the company website, job boards, referrals, or other outside sources.

3. Staff need to create and edit job openings. A job opening can be open or closed.

4. Staff need to record when a candidate applies for a job opening. A candidate may apply for several different jobs, but should not have more than one application for the same opening.

5. Applications move through a defined hiring process. The system must include these stages: Applied, Screening, Interview, Final Review, Offer, Hired, Rejected, and Withdrawn.

6. Staff need an easy way to see where applicants are in the hiring process and move them from one stage to another. Moving an applicant should not require reloading the entire page.

7. The system needs to keep track of the skills associated with each job opening. The same skill may apply to many different openings.

8. We need to decide how candidate records should be managed over time. For example, we have not decided when a candidate should be edited, archived, deactivated, or removed.

9. We need to decide what happens when a job opening closes. Existing applications may still be in progress, and an opening may or may not be allowed to reopen.