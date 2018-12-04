# ansible-role-degoss [![Build Status][travis.svg]][travis]

A system testing framework using [Ansible][ansible] and [Goss][goss] to execute system test cases against one or many
machines with minimal side-effects.

`degoss` _deploys_ your test cases to the machine, _installs_ a specified or latest version of Goss, _tests_ your
system via the defined test cases, _cleans_ by removing all Goss-related files from disk, and then _reports_ test
results to Ansible's output.

Available on Ansible Galaxy at [`naftulikay.degoss`][galaxy].

## Requirements

The `degoss` role downloads a 64-bit Linux Goss binary, but has the base requirements to be expanded to support macOS
[once Goss starts shipping macOS binaries][issue:goss-macos].

> **NOTE:** `degoss` should support any modern Linux distribution with Python 2.7 and later. Goss is a static binary
> that should be able to run on any Linux distribution, but the `degoss` role itself uses a Python module to manage the
> install, test, clean lifecycle. If you see output like ["Failed to validate the SSL certificate"][issue:ansible-ssl],
> please follow the instructions at that link to install the Python packages required to get TLS working in Python.

## License

Licensed at your discretion under either:

 - [MIT License](./LICENSE-MIT)
 - [Apache License, Version 2.0](./LICENSE-APACHE)


 [ansible]: https://github.com/ansible/ansible/
 [galaxy]: https://galaxy.ansible.com/naftulikay/degoss/
 [goss]: https://goss.rocks
 [issue:ansible-ssl]: https://github.com/ansible/ansible/issues/36791
 [issue:goss-macos]: https://github.com/aelsabbahy/goss/issues/385
 [travis.svg]: https://travis-ci.org/naftulikay/ansible-role-degoss.svg?branch=master
 [travis]: https://travis-ci.org/naftulikay/ansible-role-degoss
