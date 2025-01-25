# Makefile

.PHONY: install start stop restart logs init-local check-health

install:
	pip install -r requirements.txt

start:
	docker-compose up -d
	@echo "Waiting for LocalStack to be ready..."
	@sleep 10
	python src/infra/localstack/init/01_init_resources.py

stop:
	docker-compose down

restart: stop start

logs:
	docker-compose logs -f localstack

init-local:
	python src/infra/localstack/init/01_init_resources.py

check-health:
	curl http://localhost:4566/_localstack/health