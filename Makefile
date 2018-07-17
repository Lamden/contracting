test-db-container:
	cd docker/myrocks && docker build -t seneca-myrocks-test .

test_db_conf.ini:
	./scripts/make_test_config.py

run-test-db-container: test-db-container test_db_conf.ini
	./scripts/start_test_db.sh

kill-test-db-container:
	docker kill `docker ps --format "table {{.Names}}" --filter "ancestor=seneca-myrocks-test"| tail -n +2` || true; sleep 2

kill: kill-test-db-container

coverage:
	coverage run --source seneca seneca/test.py && coverage report -m --fail-under=100 --omit=seneca/test.py,seneca/smart_contract_tester.py

static-analysis:
	false

test:
	./seneca/test.py
