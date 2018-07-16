myrocks-docker:
	cd docker/myrocks && docker build -t seneca-myrocks-test --build-arg CACHEBUST=$$(date +%s) .

myrocks-docker-run: myrocks-docker
	cd docker/myrocks && docker run -p 3306:3306 seneca-myrocks-test &
	docker ps

myrocks-docker-kill:
	docker kill `docker ps --format "table {{.Names}}" --filter "ancestor=seneca-myrocks-test"| tail -n +2` || true; sleep 2

kill: myrocks-docker-kill
run: kill myrocks-docker-run

coverage:
	coverage run --source seneca seneca/test.py && coverage report -m --fail-under=100 --omit=seneca/test.py,seneca/smart_contract_tester.py

static-analysis:
	false

test:
	true
