#!/usr/bin/make -f

.DEFAULT_GOAL := apply
.PHONY: apply

DEFAULT_IMAGE:=centos7
IMAGE:=$(shell echo "$${IMAGE:-$(DEFAULT_IMAGE)}")

clean:
	@docker-compose rm -fs $(IMAGE)

start:
	@docker-compose up -d $(IMAGE)

shell: start
	@docker exec -it $(IMAGE) bash

dependencies: start
	@docker exec $(IMAGE) ansible --version
	@docker exec $(IMAGE) wait-for-boot
	@if [ -e tests/requirements.yml ] ; then \
		docker exec $(IMAGE) ansible-galaxy install -r /etc/ansible/roles/default/tests/requirements.yml ; \
	fi

integration-test: dependencies
	@# execute integration tests
	@docker exec $(IMAGE) env ANSIBLE_FORCE_COLOR=yes \
		ansible-playbook $(shell echo $$ANSIBLE_ARGS) /etc/ansible/roles/default/tests/playbook.yml

unit-test: dependencies
	@# execute unit tests
	@docker exec $(IMAGE) env ANSIBLE_FORCE_COLOR=yes \
		ansible-playbook $(shell echo $$ANSIBLE_ARGS) /etc/ansible/roles/default/tests/bootstrap-unit-tests.yml
	@docker exec $(IMAGE) bash -c '(cd /etc/ansible/roles/default/ && python tests.py -vvv)'


test: integration-test unit-test

prepare-apply:
	@mkdir -p target/ .ansible/galaxy-roles
	@rsync --exclude=.ansible/galaxy-roles -a ./ .ansible/galaxy-roles/rust-dev/
	@if [ -e tests/requirements.yml ]; then \
		ansible-galaxy install -p .ansible/galaxy-roles -r tests/requirements.yml ; \
	fi


apply: prepare-apply
	@ansible-playbook -i localhost, -c local --ask-become-pass local.yml

apply-ssh: prepare-apply
	@ansible-playbook -i localhost, --ask-become-pass local.yml
