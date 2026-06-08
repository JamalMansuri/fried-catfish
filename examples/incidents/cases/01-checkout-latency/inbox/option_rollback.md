# Roll back deploy 4821

From: #checkout-oncall

Revert 4821 and redeploy the previous build. It's the change that landed twelve minutes before the
spike, and it's the one thing in the window we can undo in a single command. Rolling it back
restores the old single-query path on the order-summary endpoint; if the N+1 is the cause, p99
drops immediately. Fully reversible — if it doesn't help we've lost four minutes, not an hour.
