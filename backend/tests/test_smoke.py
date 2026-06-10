import asyncio

import pytest
from fastapi import HTTPException

from app.main import ActionRequest, apply_action, health, list_review_items, reset_items


def run_async(coro):
    return asyncio.run(coro)


def test_health_check() -> None:
    assert run_async(health()) == {"status": "ok"}


def test_review_items_endpoint_returns_seed_data() -> None:
    run_async(reset_items())

    response = run_async(list_review_items())

    assert len(response["items"]) > 0


def test_active_queue_excludes_terminal_items() -> None:
    run_async(reset_items())

    response = run_async(list_review_items())
    statuses = {item["status"] for item in response["items"]}

    assert "approved" not in statuses
    assert "rejected" not in statuses
    assert "escalated" not in statuses


def test_active_queue_is_sorted_by_required_urgency() -> None:
    run_async(reset_items())

    response = run_async(list_review_items())
    ids = [item["id"] for item in response["items"]]

    assert ids[:4] == ["RV-1024", "RV-1030", "RV-1025", "RV-1032"]


def test_claim_unassigned_item_moves_it_to_in_review_and_records_reviewer() -> None:
    run_async(reset_items())

    response = run_async(
        apply_action(
            "RV-1024",
            ActionRequest(action="claim", reviewer="alex"),
        )
    )

    item = response["item"]

    assert item["status"] == "in_review"
    assert item["assigned_reviewer"] == "alex"


def test_claim_already_in_review_item_is_rejected_cleanly() -> None:
    run_async(reset_items())

    with pytest.raises(HTTPException) as error:
        run_async(
            apply_action(
                "RV-1030",
                ActionRequest(action="claim", reviewer="alex"),
            )
        )

    assert error.value.status_code == 409
    assert error.value.detail == "Only unassigned items can be claimed"


def test_decision_action_requires_in_review_status() -> None:
    run_async(reset_items())

    with pytest.raises(HTTPException) as error:
        run_async(
            apply_action(
                "RV-1024",
                ActionRequest(action="approve", reviewer="alex"),
            )
        )

    assert error.value.status_code == 409
    assert error.value.detail == "Only in-review items can be approved, rejected, or escalated"


def test_in_review_item_can_be_approved_then_becomes_terminal() -> None:
    run_async(reset_items())

    response = run_async(
        apply_action(
            "RV-1030",
            ActionRequest(action="approve", reviewer="alex"),
        )
    )

    assert response["item"]["status"] == "approved"

    with pytest.raises(HTTPException) as error:
        run_async(
            apply_action(
                "RV-1030",
                ActionRequest(action="reject", reviewer="alex"),
            )
        )

    assert error.value.status_code == 409
    assert error.value.detail == "Only in-review items can be approved, rejected, or escalated"