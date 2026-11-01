## Project 1 Applicant Tracking System

Q1- I technically don't have a class that inherits from forms.Form, however the website does use the Django AuthenticationForm so I'm using that. My ModelForm chosen is CanidateForm. 

    AuthenticationForm- Checks username and password. When it validates, it calls django's authenticate() and if anything wrong occurs, it adds an error. 

    The app uses AuthenticationForm to make sure users who are not logged in are sent to the login page(config/settings.py line 50), it also redirects users from /accounts to /accounts/login (config/urls.py line 6), and it also writes the inputs by hand, name="username" and name="password", so they match the form's field names. It shows form.non_field_errors in a DaisyUI alert, which is where the phrase "Please enter a correct username and password" appears.

    CandidateForm- It creates and edits candidate records. It has users provide an email using a text box, a source using a dropdown box, and optional fields as well (phone #, location, notes, etc.). 

    clean_email() makes it so every entered email is lowercased in order to make sure that no emails given match. 

    The app uses it in hiring/views.py lines 52-74. It helps create and edit candidate forms. 

    Differences- 
    Authentication is not tied to a model, while Candidate is. 
    Authentication cannot save given data, while Candidate can.

    Candidate is best used for storing data given by the user. Authentication is given data, but compares it to data already stored.

Q2- Job openings to skills. 

hiring/models.py line 137
skills = models.ManyToManyField(Skill, blank=True, related_name="job_openings") 

One foreign key wouldn't work because a foreign key column holds one value per row. A job opening could only look at candidates who hold only one skill instead of a vast array, or skills could only be attached to one individual job opening. 

Django made it automatically. 

Q3- The application state prototype was built to answer how applicants would be able to traverse the hiring process. The decision made was that canidates could move forward an infinite amount of space, skipping steps, but could only move back one position at a time. One alternate option I remember is being able to move forwards and backwards freely.

This decision can be seen in the section "Stage transition rules" in the PRD.