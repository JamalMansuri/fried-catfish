# Add a composite index on the order query

From: #checkout-oncall

The order-summary query is slow under load. Add a composite index covering its filter and sort
columns so each call is cheaper. Lower per-query cost takes pressure off CPU without reverting
anyone's work.
