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

test: start
	@docker exec $(IMAGE) ansible --version
	@docker exec $(IMAGE) wait-for-boot
	@if [ -e tests/requirements.yml ] ; then \
		docker exec $(IMAGE) ansible-galaxy install -r /etc/ansible/roles/default/tests/requirements.yml ; \
	fi
	@docker exec $(IMAGE) env ANSIBLE_FORCE_COLOR=yes \
		ansible-playbook $(shell echo $$ANSIBLE_ARGS) /etc/ansible/roles/default/tests/playbook.yml

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
