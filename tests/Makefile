#!/usr/bin/make -f

galaxy:
	@if [ -e requirements.yml ]; then \
		ansible-galaxy install --force -r requirements.yml -p .ansible/galaxy-roles ; \
	fi

install: galaxy
	@mkdir -p .ansible/roles
	@rsync -a --exclude=tests/ ../ .ansible/roles/default/

test: install
	@ANSIBLE_FORCE_COLOR=yes ansible-playbook -i inventory/hosts.yml playbook.yml