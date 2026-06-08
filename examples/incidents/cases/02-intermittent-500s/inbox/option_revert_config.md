# Revert the connection-pool config change

From: #api-oncall

Put the database connection pool max back to 50. The 13:20 change to 5 is the only thing in the
window, and it lines up to the minute with the first 500. Restoring the pool ends the connection
starvation; it's a one-line config revert and fully reversible.
