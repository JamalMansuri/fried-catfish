# Investigation: the timeline points at a deploy, not the box

From: #checkout-oncall, 14:40

Reading the timeline in order: p99 was flat and healthy until 14:15. Deploy 4821 went out at
14:03 — about twelve minutes before the spike began. Nothing else changed in that window.

4821 touched the order-summary endpoint. A trace on a slow request shows the page now issues one
query per line item — a classic N+1 — instead of the single batched query it used before. The CPU
isn't the cause; it's pegged *because* the query count exploded. The box was fine an hour ago and
traffic is normal for a Tuesday.
