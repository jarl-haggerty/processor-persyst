.PHONY: help test run

SERVICE_NAME  ?= "processor-EDF"

.DEFAULT: help

help:
	@echo "Make Help for $(SERVICE_NAME)"
	@echo ""
	@echo "make test			- run tests locally via docker-compose"
	@echo "make run				- run the processor locally via docker-compose"

test:
	docker-compose -f docker-compose.test.yml down --remove-orphans
	docker-compose -f docker-compose.test.yml build
	docker-compose -f docker-compose.test.yml up --exit-code-from test_edf_processor

run:
	docker-compose -f docker-compose.yml down --remove-orphans
	docker-compose -f docker-compose.yml build
	docker-compose -f docker-compose.yml up --exit-code-from edf_processor
