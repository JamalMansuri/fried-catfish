# Restore the idempotency-key guard

From: #payments-oncall

Put back the idempotency check the Thursday refactor dropped: record each `event_id` and make a
repeat delivery a no-op. This is what made retries safe before, and it lines up exactly with when
the double charges started. Restore it and legitimate retries stop double-applying.
