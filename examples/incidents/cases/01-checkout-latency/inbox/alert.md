# ALERT: checkout p99 latency 5× and climbing

From: pagerduty / #checkout-oncall

Checkout p99 latency jumped from ~180ms to over 900ms and is still climbing. The database
dashboard is red: primary CPU pegged at 98%, the slow-query log is filling up, and the connection
pool is saturated. A growing share of checkout requests are timing out before they return.
Customers are seeing spinners at "Place order" and support tickets are starting to come in.

Every symptom on the dashboard points at the database falling over under load.
