# Scale up the database

From: #checkout-oncall

The database CPU is pegged at 98% and requests are timing out — the box is clearly the bottleneck.
Fail over to a larger primary instance and add read replicas so there's CPU headroom to absorb the
load. This is the standard play when the database is saturated under traffic, and it doesn't
require first figuring out which query is hot.
