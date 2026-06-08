# Bound the cache with eviction and a TTL

From: #platform-oncall

Give the response cache a max size and a TTL so it evicts instead of growing forever. The heap
dump points straight at it; capping it makes memory plateau instead of climbing to the OOM line.
This fixes the actual leak rather than buying time.
