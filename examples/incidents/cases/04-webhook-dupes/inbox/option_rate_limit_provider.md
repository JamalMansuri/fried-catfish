# Rate-limit the provider's retries

From: #payments-oncall

The provider is re-delivering the same event two or three times, so ask them to back off and
rate-limit incoming webhook deliveries from their IPs so we only accept one delivery per event.
Stop the duplicate deliveries at the door.
