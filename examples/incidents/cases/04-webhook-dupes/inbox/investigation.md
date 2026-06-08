# Investigation: our idempotency check went missing

From: #payments-oncall

The provider re-delivering is normal and documented: they retry a webhook until they get a 200,
and our endpoint has been slow this week, so they retry more. That part is working as designed.

What changed: a refactor last Thursday removed the idempotency-key guard that used to make a repeat
delivery a no-op. Since then, every legitimate retry re-runs the charge. The provider isn't
misbehaving — our dedup is gone. The retries are a symptom; the missing idempotency key is the
cause.
