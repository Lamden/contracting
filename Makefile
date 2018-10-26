lint:
	find seneca -iname "*.py" | xargs pylint

help:
	echo '\n\n'; cat Makefile; echo '\n\n'

clean:
	bash ./scripts/clean.sh

build:
	cythonize -i --exclude="test_contracts/" ./seneca

test:
	python3 tests/run.py

venv:
	virtualenv -p python3 venv

install:
	pip3 install -r requirements.txt
	pip3 install -r dev-requirements.txt
