# Speed up the webhook endpoint

From: #payments-oncall

The provider retries because our endpoint is slow to return 200. Make the handler fast — ack
first, process async — so it stops retrying and the duplicate deliveries dry up.
