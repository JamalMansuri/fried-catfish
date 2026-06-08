# ALERT: search stale since Tuesday — indexer looks dead

From: #search-oncall

Users report that documents created since Tuesday don't appear in search. The indexer job's
dashboard shows "indexed 0 documents" on each of its last several runs. The job that's supposed to
pull in new docs is doing nothing — it looks hung or dead. The obvious move is to restart the
indexer and get it processing again.

Zero docs indexed for two days; the job needs a kick.
