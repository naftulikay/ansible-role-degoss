#!/usr/bin/make -f

SHELL:=$(shell which bash)

clean:
	@docker-compose down

build:
	@docker-compose up -d --build

start: build

pip:
	@pip install -q $(shell test -z "$$TRAVIS" && echo "--user") -r requirements.txt ; \

install: pip

unittest: pip
	@python tests.py -vvv

test: install start unittest
	@make -C tests/ test
