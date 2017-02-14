ansible-role-degoss [![Build Status][img-build-status]][build-status]
=========

Installs, runs, and removes [Goss][goss] and a Goss spec file on a system. If you'd like to lint a system without
leaving any traces, `degoss` should do what you want.

Props to upstream [ansible-goss][ansible-goss] for inspiration for the module and the majority of the plugin code.

Requirements
------------

This module downloads a 64-bit Linux Goss binary. If support for multiple operating systems and architectures is
desired, pull requests are welcome!

Role Variables
--------------

<dl>
  <dt><code>tests</code></dt>
  <dd>A Goss test file or list of files to run on the target machine.</dd>
  <dt><code>version</code></dt>
  <dd>The version string of Goss to install. Example: <code>0.2.5</code>.</dd>
</dl>

Dependencies
------------

None.

Example Playbook
----------------

Run Goss:

```
 - hosts: servers
   roles:
     - { role: degoss, tests: goss.yml }
```

Run Goss with a specific version:

```
 - hosts: servers
   roles:
     - { role: degoss, version: "0.2.5", tests: goss.yml }
```

License
-------

MIT

 [ansible-goss]: https://github.com/indusbox/goss-ansible
 [build-status]: https://travis-ci.org/naftulikay/ansible-role-degoss
 [img-build-status]: https://travis-ci.org/naftulikay/ansible-role-degoss.svg?branch=master
 [goss]: https://goss.rocks
