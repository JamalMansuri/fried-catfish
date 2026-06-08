# Open a provider ticket and harden the gateway call

From: #api-oncall

The logs are full of payments-gateway 504 timeouts, so escalate to the payments provider and, in
the meantime, wrap the gateway call in retries with a tighter timeout so one slow upstream call
doesn't 500 the whole request. The failures are all on their side of the wire.
