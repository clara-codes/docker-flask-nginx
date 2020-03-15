include unit_test.env
image:
	docker build -t order-api .
docker-compose:
	docker-compose --file docker-compose.yml up -d
test-integration:
	python tests/integration_tests/tests_db.py
	python tests/integration_tests/tests_place_order_db.py
	python tests/integration_tests/tests_take_order_db.py
test-unit:
	export $(shell sed 's/=.*//' unit_test.env)
	python tests/unit_tests/tests_place_order.py
	python tests/unit_tests/tests_take_order.py
test-load:
	locust -f tests/integration_tests/load_tests/tests_take_order_load.py