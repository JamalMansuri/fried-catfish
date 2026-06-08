# Send a non-null default for the new field

From: #mobile-oncall

Patch the backend to always populate `loyalty_tier` with a default instead of null. The old app
crashes only on null; give it a value and every existing build — cached responses included — stops
crashing immediately, without waiting on an app-store release or a full rollback.
