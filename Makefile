myrocks-docker:
	cd docker/myrocks && docker build -t seneca-myrocks-test .

myrocks-docker-run: myrocks-docker check-docker-run-args
	cd docker/myrocks && docker run -dp 3306:3306 seneca-myrocks-test $(db_user) $(db_password) $(db_db_name)
	docker ps

check-docker-run-args:
	ifndef db_user 
	  $(error db_user is undefined)
	endif
	ifndef db_password
	  $(error db_password is undefined)
	endif
	ifndef db_db_name
	  $(error db_db_name is undefined)
	endif

myrocks-docker-kill:
	docker kill `docker ps --format "table {{.Names}}" --filter "ancestor=seneca-myrocks-test"| tail -n +2` || true; sleep 2

kill: myrocks-docker-kill
run: kill myrocks-docker-run

coverage:
	coverage run --source seneca seneca/test.py && coverage report -m --fail-under=100 --omit=seneca/test.py,seneca/smart_contract_tester.py

static-analysis:
	false

test:
	false
