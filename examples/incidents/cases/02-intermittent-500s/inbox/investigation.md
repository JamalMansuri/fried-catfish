# Investigation: the pool, not the provider

From: #api-oncall, 14:05

Timeline: the 500s started at 13:20, to the minute. The only thing that shipped then was a config
change tagged "harmless tuning" that dropped the database connection pool max from 50 to 5.

Under afternoon traffic, requests now queue waiting for one of five connections. The payments call
is the slowest downstream hop, so it's where the wait crosses the timeout and surfaces as a 504 —
but the provider's status page is green and their own latency is flat. We're starving ourselves of
connections; the gateway timeout is the symptom, not the cause.
