# Schedule a rolling restart every 24h

From: #platform-oncall

Since memory climbs predictably, add a cron that rolls the pods every 24 hours to stay under the
OOM limit. Crude, but it keeps the service up.
