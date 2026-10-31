from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CandidateForm
from .models import Candidate
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
