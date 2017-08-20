#!/usr/bin/make -f
ROLE_NAME:=degoss
MOUNT_PATH:=/etc/ansible/roles/$(ROLE_NAME)

# TODO trusty needs not systemd flags
SYSTEMD_FLAGS:=--privileged -v /sys/fs/cgroup:/sys/fs/cgroup:ro

LOCAL_FLAGS:=-v $(shell pwd):$(MOUNT_PATH):ro -v $(shell pwd)/ansible.cfg:/etc/ansible/ansible.cfg:ro
SELINUX_FLAGS:=

CONTAINER_ID_DIR:=/tmp/container/$(IMAGE_NAME)
CONTAINER_ID_FILE:=$(CONTAINER_ID_DIR)/id
CONTAINER_ID:=$(shell cat "$(CONTAINER_ID_FILE)" 2>/dev/null)

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
	docker exec -it $(CONTAINER_ID) /bin/bash -

test:
	@if [ -z "$(CONTAINER_ID)" ]; then \
		echo "ERROR: Container Not Running" >&2 ; \
		exit 1 ; \
	fi
	@# need a way to ask systemd in the container to wait until all services up
	docker exec $(CONTAINER_ID) ansible --version
	docker exec $(CONTAINER_ID) wait-for-boot
	test -f ${MOUNT_PATH}/tests/requirements.yml && \
		docker exec $(CONTAINER_ID) ansible-galaxy install -r ${MOUNT_PATH}/tests/requirements.yml || true
	docker exec $(CONTAINER_ID) env ANSIBLE_FORCE_COLOR=yes \
		ansible-playbook -v $(MOUNT_PATH)/tests/playbook.yml

test-clean:
	$(MAKE) restart
	$(MAKE) test
