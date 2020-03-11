image:
	docker build -t order-api .
docker-compose:
	docker-compose --file docker-compose.yml up -d
test-integration:
	cd /home && python tests/integration_tests/tests_db.py