# Cache the order-summary response

From: #checkout-oncall

Put a short-TTL cache in front of the order-summary endpoint so repeated reads skip the database
entirely. Fewer queries, less CPU, and it keeps the new deploy in place.
