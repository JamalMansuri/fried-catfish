# Investigation: a null the old app can't parse

From: #mobile-oncall

The crashes are entirely on app build 4.2.0 and older; build 4.3.0 doesn't crash at all. Deploy
5102 added a new field, `loyalty_tier`, to the profile response, and it's nullable. The old app's
JSON decoder declared that field non-optional, so it crashes when the value is null. Newer builds
handle it.

So the deploy is the trigger, but rolling the backend back only stops *new* null responses —
clients that already cached one still crash, and you can't roll back the app store. The clean fix
is server-side: always send a non-null default for `loyalty_tier` so old clients never see null.
