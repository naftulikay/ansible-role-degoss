#!/usr/bin/make -f

SHELL:=$(shell which bash)

clean:
	@docker-compose down

start:
	@docker-compose up -d

pip:
	@pip install -q $(shell test -z "$$TRAVIS" && echo "--user") -r requirements.txt ; \

docs: pip
	@make -C docs/ html

serve: pip
	@sphinx-reload --host 0.0.0.0 --port 5500 docs/

install: pip

unittest: pip
	@if [ -e tests.py ]; then python tests.py -vvv ; fi

test: install start unittest docs
	@make -C tests/ test
