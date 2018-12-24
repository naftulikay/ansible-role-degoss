#!/usr/bin/make -f

install:
	@mkdir -p .ansible/roles
	@rsync -a --exclude=tests/ ../ .ansible/roles/default/

test: install
	@ANSIBLE_FORCE_COLOR=yes ansible-playbook -i inventory/hosts.yml playbook.yml
