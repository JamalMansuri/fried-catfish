# Investigation: an old cache with no ceiling

From: #platform-oncall

A heap dump at 80% utilization says ~90% of retained bytes are one process-local response cache —
a plain map that only ever grows, no eviction, no TTL. Git history puts that cache at three weeks
old, not yesterday.

Plot RSS over the last 21 days and the slope is a straight line, straight through yesterday's flag
rollout. The flag correlates with when a human first noticed the OOMs, not with the memory slope.
The unbounded cache just finally crossed the limit this week.
