# Makefile

.PHONY: install start stop restart logs init-local check-health start-local stop-local create-bucket test test-unit test-integration test-coverage

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

start-local:
	docker-compose up -d
	sleep 5
	awslocal s3 mb s3://runctl-raw-data || true

stop-local:
	docker-compose down

create-bucket:
	awslocal s3 mb s3://runctl-raw-data || true

test: test-unit test-integration

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

test-coverage:
	pytest --cov=src --cov-report=html tests/
	@echo "Coverage report generated in htmlcov/index.html"