# ALERT: intermittent 500s on the API since 13:20

From: pagerduty / #api-oncall

The API error rate climbed from near-zero to ~4% of requests just after 13:00 — all 500s, and
intermittent: a request fails, the retry often succeeds. The error logs are dominated by one line,
`payments-gateway: upstream timeout (504)`. Every failing request is the one waiting on the
payments provider and giving up.

Looks like the payments provider is flaky again and dragging checkout down with it.
