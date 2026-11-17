.PHONY: test run install version qa shot

test:
	PYTHONPATH=. python3 -m unittest discover -s tests -v

run:
	./bin/hyprtk-edit

install:
	./install.sh

version:
	PYTHONPATH=. python3 -m hyprtk_editor --version

qa:
	./scripts/qa.sh

shot:
	python3 scripts/screenshot.py shot.png
