# demo/catfish.tape — raw terminal capture (charmbracelet/vhs).  make demo  re-renders + post-zooms.
# Offline & deterministic via CATFISH_DEMO=1 — no API key, canned model outputs, REAL control flow.
# Paced reveal + color, then the run CLEARS to a focused "THE CALL" panel. The cinematic zoom-in and
# the long hold are added afterward by demo/zoom.sh (ffmpeg) — VHS itself has no camera move.

Output demo/_raw.gif

Set Shell "bash"
Set FontSize 18
Set Width 1280
Set Height 1080
Set Padding 28
Set TypingSpeed 40ms

# --- hidden setup: offline + paced + colored demo mode + a clean `catfish` command ---
Hide
Type "export CATFISH_DEMO=1 CATFISH_DEMO_PACED=1 CATFISH_DEMO_COLOR=1 CATFISH_DEMO_PACE_SEC=1.5 CATFISH_DEMO_REPORT_PACE=1.2 PYTHONPATH=src"
Enter
Type 'catfish() { python3 -m catfish "$@"; }'
Enter
Type "clear"
Enter
Show

# Cold open — set the scene.
Type "# Arrakis. The Fremen await one word from Muad'Dib: jihad."
Sleep 1000ms
Enter
Sleep 1000ms

# The messy context: council reports, a mentat threat tally, the vision, a warning.
Type "ls examples/inbox/"
Sleep 400ms
Enter
Sleep 2000ms

# One impossible question -> a real tournament -> one focused, human-gated call.
Type 'catfish tournament examples/inbox "Do we unleash the Fremen jihad across the Imperium?" --finalists 4 --decide A --by "Paul Atreides"'
Sleep 700ms
Enter

# Paced reveal (GENERATION -> REFLECTION -> RANKING + cycle -> BRADLEY-TERRY), then it clears and types
# out the real DECISION REPORT (sources -> grounded reasoning -> machine proposed / human decided ->
# recorded). Land on the finished report; zoom.sh adds a gentle push-in and the 10s+ hold.
Sleep 16000ms
