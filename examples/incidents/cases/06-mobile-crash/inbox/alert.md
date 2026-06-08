# ALERT: mobile crash rate 8× since the 09:05 deploy

From: pagerduty / #mobile-oncall

Mobile crash rate jumped 8× starting at 09:10. Backend deploy 5102 went out at 09:05 — the timing
lines up almost exactly. Crashes climbed the moment the deploy finished rolling. The obvious move
is to roll back 5102 and stop the bleeding.

The deploy and the crash spike are five minutes apart; roll it back.
