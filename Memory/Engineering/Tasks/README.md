# Barrymore Task Ledger

This folder is the durable source of task status shown in the Barrymore Morning Brief.
Engineering plan stages remain in `../PLAN.md`; the ledger starts with the five
urgent/regular items previously shown on the dashboard plaque.

## Lifecycle

- One task is one JSON file in `Active/`, named with its stable lowercase ID.
- `status` is `active` or `done`. Only the explicit **Mark Done** action in the
  local dashboard changes an active task to done.
- Every task record keeps its `history` array. The Done action adds a timestamped
  event and `completedAt`; it does not erase the task or its prior history.
- Done tasks remain in `Active/` and in the brief for 48 hours. On the next
  dashboard task check after that period (once a minute while the dashboard is
  open, otherwise at its next visit), the complete record moves to
  `Archive/YYYY/MM/`, with an `archivedAt` timestamp and an archive event.

## Adding a task

Create a JSON file in `Active/` with a unique ID and this shape:

```json
{
  "id": "review-sample",
  "title": "Review sample",
  "source": "User",
  "priority": "regular",
  "status": "active",
  "createdAt": "2026-10-29T04:26:16Z",
  "history": [
    {
      "status": "active",
      "at": "2026-10-29T04:26:16Z"
    }
  ]
}
```

Use an ISO-8601 UTC timestamp (`Z` suffix), `urgent` or `regular` priority, and
never reuse an ID from `Archive/`.
