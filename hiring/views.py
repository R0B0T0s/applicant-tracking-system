from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CandidateForm, JobOpeningForm, SkillForm
from .models import Candidate, JobOpening, Skill
from .permissions import hiring_manager_required


def home(request):
    return render(request, "hiring/home.html")


@hiring_manager_required
def manager_tools(request):
    return render(request, "hiring/manager_tools.html")


def candidate_list(request):
    q = request.GET.get("q", "").strip()
    show_archived = bool(request.GET.get("show_archived"))
    candidates = Candidate.objects.all()
    if not show_archived:
        candidates = candidates.filter(is_archived=False)
    if q:
        candidates = candidates.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )
    return render(
        request,
        "hiring/candidate_list.html",
        {"candidates": candidates, "q": q, "show_archived": show_archived},
    )


def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    return render(request, "hiring/candidate_detail.html", {"candidate": candidate})


def candidate_create(request):
    if request.method == "POST":
        form = CandidateForm(request.POST)
        if form.is_valid():
            candidate = form.save()
            return redirect(candidate)
    else:
        form = CandidateForm()
    return render(request, "hiring/candidate_form.html", {"form": form})


def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == "POST":
        form = CandidateForm(request.POST, instance=candidate)
        if form.is_valid():
            form.save()
            return redirect(candidate)
    else:
        form = CandidateForm(instance=candidate)
    return render(
        request, "hiring/candidate_form.html", {"form": form, "candidate": candidate}
    )


@hiring_manager_required
def candidate_archive(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == "POST":
        candidate.is_archived = True
        candidate.archived_at = timezone.now()
        candidate.save()
        return redirect(candidate)
    return render(
        request,
        "hiring/candidate_archive_confirm.html",
        {"candidate": candidate, "archiving": True},
    )


@hiring_manager_required
def candidate_unarchive(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == "POST":
        candidate.is_archived = False
        candidate.archived_at = None
        candidate.save()
        return redirect(candidate)
    return render(
        request,
        "hiring/candidate_archive_confirm.html",
        {"candidate": candidate, "archiving": False},
    )


def job_list(request):
    q = request.GET.get("q", "").strip()
    jobs = JobOpening.objects.select_related("hiring_manager")
    if q:
        jobs = jobs.filter(
            Q(title__icontains=q)
            | Q(department__icontains=q)
            | Q(location__icontains=q)
        )
    return render(request, "hiring/job_list.html", {"jobs": jobs, "q": q})


def job_detail(request, pk):
    job = get_object_or_404(
        JobOpening.objects.select_related("hiring_manager").prefetch_related("skills"),
        pk=pk,
    )
    return render(request, "hiring/job_detail.html", {"job": job})


def job_create(request):
    if request.method == "POST":
        form = JobOpeningForm(request.POST)
        if form.is_valid():
            job = form.save()
            return redirect(job)
    else:
        form = JobOpeningForm()
    return render(request, "hiring/job_form.html", {"form": form})


def job_edit(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    if request.method == "POST":
        form = JobOpeningForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect(job)
    else:
        form = JobOpeningForm(instance=job)
    return render(request, "hiring/job_form.html", {"form": form, "job": job})


@hiring_manager_required
def skill_list(request):
    skills = Skill.objects.annotate(job_count=Count("job_openings"))
    return render(request, "hiring/skill_list.html", {"skills": skills})


@hiring_manager_required
def skill_create(request):
    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("hiring:skill_list")
    else:
        form = SkillForm()
    return render(request, "hiring/skill_form.html", {"form": form})


@hiring_manager_required
def skill_edit(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    if request.method == "POST":
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            return redirect("hiring:skill_list")
    else:
        form = SkillForm(instance=skill)
    return render(request, "hiring/skill_form.html", {"form": form, "skill": skill})


@hiring_manager_required
def skill_delete(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    if request.method == "POST":
        skill.delete()
        return redirect("hiring:skill_list")
    return render(
        request,
        "hiring/skill_delete_confirm.html",
        {"skill": skill, "job_count": skill.job_openings.count()},
    )
