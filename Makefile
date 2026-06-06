.PHONY: demo test help

help:  ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-8s %s\n", $$1, $$2}'

demo:  ## record + post-zoom the README demo GIF -> demo/catfish.gif (needs: vhs, ffmpeg)
	vhs demo/catfish.tape
	bash demo/zoom.sh

test:  ## run the test suite in offline demo mode
	CATFISH_DEMO=1 PYTHONPATH=src python3 -m pytest -q
