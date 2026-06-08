# ALERT: pods OOM-killing every ~36 hours

From: pagerduty / #platform-oncall

The recommendations service climbs in memory steadily and gets OOM-killed roughly every 36 hours,
then restarts clean and climbs again. It started getting noticed right after yesterday's feature
flag rollout for the new "related items" widget — the newest change is the obvious suspect.

Memory is the symptom; the flag is what shipped yesterday.
