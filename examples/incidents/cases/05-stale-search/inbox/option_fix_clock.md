# Fix the clock skew and reset the watermark

From: #search-oncall

Restore NTP on the drifted worker and reset the indexer watermark back to real time. The skew is
why every new doc reads as "already processed." Once the clock and watermark are correct, the next
run picks up everything created since Tuesday. This is the actual cause, not the symptom.
