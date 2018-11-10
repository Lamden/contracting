lint:
	find seneca -iname "*.py" | xargs pylint

help:
	echo '\n\n'; cat Makefile; echo '\n\n'

clean:
	bash ./scripts/clean.sh

build-cython: clean
	cythonize -i ./seneca/engine ./seneca/constants ./seneca/libs

test: start-server
	python3 tests/run.py

venv:
	virtualenv -p python3 venv

install:
	pip3 install -r requirements.txt
	pip3 install -r dev-requirements.txt

build-image:
	docker build -t seneca_base -f ./docker/seneca_base .

start-server:
	bash ./scripts/start.sh

start-docker:
	docker rm -f seneca || true
	docker run --rm -v $$(pwd):/app --name seneca --security-opt apparmor=docker-default seneca_base &
	sleep 1
	docker exec -ti seneca /bin/bash

kill-docker:
	docker kill `docker ps -q` || true; sleep 2
