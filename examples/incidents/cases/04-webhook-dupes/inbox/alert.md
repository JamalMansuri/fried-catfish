# ALERT: customers charged twice — duplicate webhook deliveries

From: pagerduty / #payments-oncall

Support has a dozen tickets for double charges this morning. The webhook logs show the same
`event_id` from the payment provider delivered two or three times within a few seconds, and each
delivery results in a charge. From the logs it reads like the provider is in a retry storm and
re-sending the same events at us.

The duplicates are all coming from the provider's side of the wire.
