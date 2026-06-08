# Raise the payments client timeout

From: #api-oncall

The calls are timing out, so increase the client timeout on the payments gateway to give slow
calls room to finish instead of returning a 500.
