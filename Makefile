image:
	docker build -t order-api .
docker-compose:
	docker-compose --file docker-compose.yml up -d 