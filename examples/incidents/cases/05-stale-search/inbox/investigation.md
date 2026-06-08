# Investigation: a clock, not a dead job

From: #search-oncall

The indexer isn't hung — it runs every five minutes, exits 0, and processes 0 because it asks the
database for "documents updated since my last watermark," and the watermark is in the future.

One indexer worker's clock drifted about +7 minutes after NTP failed on that host on Tuesday. It
stamped a watermark seven minutes ahead of real time, so every genuinely new document still looks
"already processed" and gets skipped. The "indexed 0 documents" line is correct behavior given a
bad clock — restarting the job changes nothing because the watermark survives a restart.
