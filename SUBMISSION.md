# Submission

## Summary of changes

I focused on making the reviewer workflow correct, predictable, and easier to understand. The backend now enforces the required workflow state transitions, the active queue excludes terminal items, and queue ordering follows the required urgency rules. The frontend now disables invalid actions and explains what the reviewer can do next.

## Bugs fixed

* The active queue now excludes `approved`, `rejected`, and `escalated` items.
* Queue ordering now follows risk level, customer tier, and age.
* `claim` is only allowed for `unassigned` items.
* `approve`, `reject`, and `escalate` are only allowed for `in_review` items.
* Terminal items reject further workflow actions with a clean `409` response.
* After a terminal decision in the UI, the item is removed from the active queue.

## Product and UX decisions

I added action guidance in the detail panel so reviewers are not encouraged to click workflow actions that the backend will reject. I prioritised this over broader visual improvements because incorrect workflow actions are higher risk for an internal operations tool.

The UI now reflects the workflow state of the selected item:

* `unassigned` items can only be claimed.
* `in_review` items can be approved, rejected, or escalated.
* Terminal items cannot receive further actions.

This keeps the reviewer experience aligned with the backend business rules.

## Tests added

I added backend tests for:

* Active queue filtering.
* Required urgency ordering.
* Claiming an unassigned item.
* Rejecting claims on already in-review items.
* Rejecting decision actions on non-in-review items.
* Preventing further action after an item becomes terminal.

All backend tests pass locally.

```text
8 passed
```

## Known gaps

* I did not add persistent storage.
* I did not add authentication.
* I did not add frontend test coverage.
* I kept the current reviewer identity hardcoded as `alex`, as allowed by the brief.
* I kept the scope intentionally small to stay within the timebox.

## Files changed and why

* `backend/app/main.py`: centralised queue filtering, queue ordering, and workflow action validation.
* `backend/tests/test_smoke.py`: added targeted business-rule tests for high-risk behaviour.
* `frontend/src/App.vue`: disabled invalid actions, added reviewer guidance, and removed terminal items from the active queue after a final decision.

## AI assistance used