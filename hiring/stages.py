"""Pure stage-transition rules. No Django imports; stages are plain strings."""

APPLIED = "applied"
SCREENING = "screening"
INTERVIEW = "interview"
FINAL_REVIEW = "final_review"
OFFER = "offer"
HIRED = "hired"
REJECTED = "rejected"
WITHDRAWN = "withdrawn"

# In pipeline order.
ACTIVE_STAGES = [APPLIED, SCREENING, INTERVIEW, FINAL_REVIEW, OFFER]
FINAL_STAGES = [HIRED, REJECTED, WITHDRAWN]

# Not a stage: a move target meaning "back to the stage before this one".
REOPEN = "reopen"


def allowed_moves(stage, can_reopen=False):
    """Return the stages an application in `stage` may move to, in display order."""
    if stage in FINAL_STAGES:
        return [REOPEN] if can_reopen else []
    if stage not in ACTIVE_STAGES:
        return []
    position = ACTIVE_STAGES.index(stage)
    # Back exactly one stage, or forward any number of stages up to Offer.
    moves = ACTIVE_STAGES[max(position - 1, 0) : position]
    moves += ACTIVE_STAGES[position + 1 :]
    if stage == OFFER:
        moves.append(HIRED)
    return moves + [REJECTED, WITHDRAWN]


def is_allowed(from_stage, to_stage, can_reopen=False):
    return to_stage in allowed_moves(from_stage, can_reopen)
