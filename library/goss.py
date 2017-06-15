#!/usr/bin/env python

import os
from ansible.module_utils.basic import *

DOCUMENTATION = '''
---
module: goss
author: Naftuli Kay
short_description: Execute a Goss Test
description:
  - Executes a Goss test. Changed always false if tests succeeded
options:
  path:
    required: true
    description:
      - A Goss test file to execute, locally available on the remote machine.
  format:
    required: false
    default: rspecish
    choices: [rspecish, documentation, json, tap, junit, nagios, nagios_verbose, silent]
    description:
      - Modify the Goss output format.
  executable:
    required: false
    default: goss
    description:
      - The executable to use when invoking Goss.
  env_vars:
    required: false
    default: \{\}
    description:
      - A map of environment variables to set when running Goss.

examples:
  - name: execute goss file
    goss: path=/path/to/file.yml

  - name: execute goss file with json output
    goss: path=/path/to/file.yml format=json

  - name: custom goss
    goss: path=/path/to/file.yml executable=/tmp/goss
'''

GOSS_OUTPUT_FORMATS = ("rspecish", "documentation", "json", "tap", "junit", "nagios", "nagios_verbose", "silent")

# launch goss validate command on the file
def evaluate(module, test_file, output_format, executable, env_vars):
    return module.run_command(
        "{0} -g {1} validate --format {2}".format(executable, test_file, output_format),
        environ_update=env_vars
    )

def succeed(module, **kwargs):
    module.exit_json(changed=False, failed=False, goss_failed=False, **kwargs)

def fail(module, message, **kwargs):
    module.fail_json(msg=message, failed=True, goss_failed=True, **kwargs)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True, type='str'),
            format=dict(required=False, type='str', choices=GOSS_OUTPUT_FORMATS),
            executable=dict(required=False, type='str', default='goss'),
            env_vars=dict(required=False, type='dict', default={})
        ),
        supports_check_mode=False
    )

    test_file = os.path.expanduser(module.params['path'])  # test file path
    fmt = module.params['format']  # goss output format
    executable = module.params['executable']
    env_vars = module.params['env_vars'] or {}

    if not test_file or len(test_file) == 0:
        fail(module, "Goss test file is undefined.")

    # test if test file is a directory
    if os.path.isdir(test_file):
        fail(module, "Goss test file {} cannot be a directory.".format(test_file))

    # test if the test file is readable
    if not os.access(test_file, os.R_OK):
        fail(module, "Goss test file {} is not readable.".format(test_file))

    # sanitize the environment variables
    for key, value in env_vars.items():
        env_vars.update(**{ key: str(value) })

    rc, stdout, stderr = evaluate(module, test_file, fmt, executable, env_vars)

    result = dict(rc=rc, stdout=stdout, stderr=stderr)

    succeed(module, **result) if rc == 0 else fail(module, "Goss Tests Failed.", **result)


if __name__ == "__main__":
    main()
