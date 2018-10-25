lint:
	find seneca -iname "*.py" | xargs pylint

help:
	echo '\n\n'; cat Makefile; echo '\n\n'

clean:
	bash ./scripts/clean.sh

build:
	cythonize -i --exclude="test_contracts/" ./seneca
