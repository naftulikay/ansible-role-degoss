#!/usr/bin/make -f
SHELL:=/bin/bash

ROLE_NAME:=degoss
MOUNT_PATH:=/etc/ansible/roles/$(ROLE_NAME)
SYSTEMD_FLAGS:=--privileged -v /sys/fs/cgroup:/sys/fs/cgroup:ro
LOCAL_FLAGS:=-v $(shell pwd):$(MOUNT_PATH):ro -v $(shell pwd)/ansible.cfg:/etc/ansible/ansible.cfg:ro
SELINUX_FLAGS:=

CONTAINER_ID_DIR:=/tmp/container/$(IMAGE_NAME)
CONTAINER_ID_FILE:=$(CONTAINER_ID_DIR)/id
CONTAINER_ID:=$(shell cat "$(CONTAINER_ID_FILE)" 2>/dev/null)

PLAYBOOK_LOG_FILE=$(CONTAINER_ID_DIR)/lastrun.log
PLAYBOOK_RC_FILE=$(CONTAINER_ID_DIR)/rc

ROLE_FLAGS:=-e degoss_no_clean=true -e degoss_debug=true

validate:
ifeq ($(IMAGE_NAME),)
	@echo "IMAGE_NAME is undefined, please define it."
	@exit 1
endif
ifeq ($(ROLE_NAME),)
	@echo "ROLE_NAME is undefined, please define it."
	@exit 1
endif

# get status of the vm-like container
status: validate
	@if [ -z "$(CONTAINER_ID)" ]; then \
		echo "Container Not Running" ; \
		exit 1 ; \
	else \
		echo "Container Running" ; \
	fi

start: validate
	@if [ ! -z "$(CONTAINER_ID)" ]; then \
		echo "ERROR: Container Already Running: $(CONTAINER_ID)" >&2 ; \
		exit 1 ; \
	fi
	@# start it
	@echo "Starting the Container:"
	@test -d "$(CONTAINER_ID_DIR)" || mkdir -p "$(CONTAINER_ID_DIR)"
	docker pull $(IMAGE_NAME)
	docker run -d $(SYSTEMD_FLAGS) $(LOCAL_FLAGS) $$(test -d /etc/selinux && echo $(SELINUX_FLAGS)) $(IMAGE_NAME) > $(CONTAINER_ID_FILE)

stop: validate
	@if [ -z "$(CONTAINER_ID)" ] && ! docker ps --filter id=$(CONTAINER_ID) --format '{{.ID}}' | grep -qP '.*' ; then \
		echo "ERROR: Container Not Running" >&2 ; \
		rm -f $(CONTAINER_ID_FILE) ; \
		exit 0 ; \
	fi ; \
	docker kill $(CONTAINER_ID) > /dev/null ; \
	docker rm -f -v $(CONTAINER_ID) > /dev/null ; \
	rm -f $(CONTAINER_ID_FILE) ; \
	echo "Stopped Container $(CONTAINER_ID)"

restart:
	$(MAKE) stop
	$(MAKE) start

shell: status
	docker exec -it $(CONTAINER_ID) /bin/bash

install-galaxy:
	@# only run ansible galaxy if need be
	@test -e tests/requirements.yml && \
		docker exec -it $(CONTAINER_ID) ansible-galaxy install -r ${MOUNT_PATH}/tests/requirements.yml || true

display-ansible-version:
	@# display the version of ansible we're working with
	docker exec $(CONTAINER_ID) ansible --version

test: status
	@# need a way to ask systemd in the container to wait until all services up
	docker exec $(CONTAINER_ID) ansible --version
	docker exec $(CONTAINER_ID) wait-for-boot

	@# TODO idempotency and clean state between tests
	$(MAKE) test-0000-pass
	$(MAKE) test-0001-fail

test-0000-pass:
	@# execute the playbook in a passing mode
	docker exec -it $(CONTAINER_ID) env ANSIBLE_FORCE_COLOR=yes ansible-playbook $(ROLE_FLAGS) $(MOUNT_PATH)/tests/playbook.yml

test-0001-fail:
	@# execute the playbook in a failing mode; has to run in subshell because of wonky tee return codes
	@( docker exec -it $(CONTAINER_ID) env ANSIBLE_FORCE_COLOR=yes \
			ansible-playbook -e should=fail $(ROLE_FLAGS) $(MOUNT_PATH)/tests/playbook.yml \
				; echo $$? > $(PLAYBOOK_RC_FILE) ; \
	) | tee $(PLAYBOOK_LOG_FILE)

	@# check that the playbook failed
	@playbook_rc=$$(cat $(PLAYBOOK_RC_FILE)) ; \
	if [ -z "$${playbook_rc}" -a "$${playbook_rc}" != "0" ]; then \
		echo "ERROR: Playbook was expected to fail and had a zero return status." >&2 ; \
		exit 1 ; \
	fi

	@# evaluate that the number of tests failed is greater than 0
	@failed_count=$$(grep -oP '(?<=Failed:\s)(\d+)' $(PLAYBOOK_LOG_FILE) | tail -n 1) ; \
	if [ $$failed_count -ne 2 ]; then \
		echo "ERROR: No tasks failed, expected at least two failures." >&2 ; \
		exit 1 ; \
	fi

	@# I don't care anymore, but this comes out in bold green
	@echo -e "$$(tput setaf 2 && tput bold)SUCCESS: Failed as per expectations; rc=$$(cat $(PLAYBOOK_RC_FILE)), failures=$$(grep -oP '(?<=Failed:\s)(\d+)' $(PLAYBOOK_LOG_FILE) | tail -n 1).$$(tput sgr0)"

test-clean:
	$(MAKE) restart
	$(MAKE) test
