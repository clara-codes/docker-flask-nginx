include unit_test.env
image:
	docker build -t order-api .
docker-compose:
	docker-compose --file docker-compose.yml up -d
test-integration:
	cd /home && python tests/integration_tests/tests_db.py
	python tests/integration_tests/tests_place_order_db.py
test-unit:
	export $(shell sed 's/=.*//' unit_test.env)
	cd /home && python tests/unit_tests/tests_place_order.py