test-db-container:
	cd docker/myrocks && docker build -t seneca-myrocks-test .

test_db_conf.ini:
	./scripts/make_test_config.py

run-test-db-container: test-db-container test_db_conf.ini
	./scripts/start_test_db.sh

console-test-db-container: test-db-container
	docker run -it --entrypoint=/bin/bash seneca-myrocks-test

connect-db:
	./scripts/connect_mysql_client.sh

kill-test-db-container:
	docker kill `docker ps --format "table {{.Names}}" --filter "ancestor=seneca-myrocks-test"| tail -n +2` || true; sleep 2

kill: kill-test-db-container

coverage:
	coverage run --source seneca seneca/test.py && coverage report -m --fail-under=85 --omit=seneca/test.py,seneca/smart_contract_tester.py

lint:
	find seneca -iname "*.py" | xargs pylint

static-analysis:
	false

test:
	./seneca/test.py

help:
	echo '\n\n'; cat Makefile; echo '\n\n'
