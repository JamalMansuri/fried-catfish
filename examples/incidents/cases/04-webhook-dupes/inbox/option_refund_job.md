# Run a reconciliation job to refund duplicates

From: #payments-oncall

Write a nightly job that scans for charges with the same `event_id` and auto-refunds the extras.
It cleans up the double charges after the fact without touching the webhook path.
