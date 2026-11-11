from backend.agent import assign_priority, needs_review


def test_safety_related_ticket_is_urgent():
    result = assign_priority({"subject": "Unsafe product", "description": "I was injured by the product."})
    assert result["priority"] == "Urgent"


def test_angry_ticket_is_high_priority():
    result = assign_priority({"subject": "Complaint", "description": "I am furious.", "sentiment": "Angry"})
    assert result["priority"] == "High"


def test_low_priority_does_not_require_human_review():
    state = {"priority": "Low"}
    assert needs_review(state) == "draft_response"


def test_high_priority_requires_human_review():
    state = {"priority": "High"}
    assert needs_review(state) == "human_review"
