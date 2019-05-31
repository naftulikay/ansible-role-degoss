#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from ansible.module_utils import six
from ansible.module_utils.basic import *

import json
import logging
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile


if six.PY3:
    from io import StringIO
    from urllib.request import Request, urlopen
else:
    from StringIO import StringIO
    from urllib2 import Request, urlopen


DOCUMENTATION = """
---
module: degoss
author: Naftuli Kay <me@naftuli.wtf>
short_description: Download, execute, and remove Goss against test cases.
description:
    - Download, execute, and remove Goss against test cases located on disk.
options:
    clean:
        type: bool
        required: false
        default: true
        description: If true, tmp_dir will be recursively removed at the end of the run.
    clean_on_failure:
        type: bool
        required: false
        default: true
        description: If false, degoss will not remove the temporary directory on a failed run.
    debug:
        type: bool
        required: false
        default: false
        description: Set the logger level to debug instead of the default, which is info.
    facts:
        type: dict
        required: false
        default: empty dictionary
        description: A dictionary of Ansible facts to securely pass into the Goss execution.
    test_dir:
        type: path
        required: true
        description: The directory in which test files are located.
    test_file:
        type: str
        required: true
        description: The test file to execute Goss against.
    tmp_root:
        type: path
        required: true
        description: The temporary root directory to remove after running.
    variables:
        type: dict
        required: false
        default: empty dictionary
        description: A dictionary of variables to pass into the Goss execution.
    version:
        type: str
        required: false
        default: latest
        description: If latest, the latest available Goss version, otherwise the specified version, e.g. 0.3.6.
examples: []
"""

BOOLEAN_TRUE_MATCHER = re.compile(r'(true|yes|on)', re.I)
BUFFER_SIZE=8192
CONSOLE_LOGGING_FORMAT = '[%(levelname)-5s] %(message)s'
DISK_LOGGING_FORMAT = '%(asctime)s [%(levelname)-5s] %(name)s: %(message)s'
REPO_URL = "https://github.com/aelsabbahy/goss"


def main(argv=sys.argv):
    """Main entrypoint into the module, instantiates and executes the service."""
    Degoss(argv, AnsibleModule(
        argument_spec=dict(
            clean=dict(type='bool', required=False, default=True),
            clean_on_failure=dict(type='bool', required=False, default=True),
            debug=dict(type='bool', required=False, default=False),
            facts=dict(type='dict', required=False, default='{}'),
            test_dir=dict(type='path', required=True),
            test_file=dict(type='str', required=True),
            tmp_root=dict(type='path', required=True),
            variables=(dict(type='dict', required=False, default='{}')),
            version=dict(type='str', required=False, default='latest'),
        )
    )).execute()


class Degoss(object):

    def __init__(self, argv, module):
        """Constructor for a Degoss service."""
        # instantiate independent variables first
        self.argv = argv
        self.log_output = StringIO()
        self.module = module

        # establish input parameters
        self.debug = self.get_bool('debug', False)
        self.clean_on_failure = module.params.get('clean_on_failure')
        self.do_clean = self.get_bool('clean', True)
        self.facts = self.module.params.get('facts', {})
        self.requested_version, self._version = module.params.get('version', 'latest'), None
        self.test_dir = self.module.params.get('test_dir')
        self.test_file = self.module.params.get('test_file').split(os.sep)[-1]
        self.tmp_root = self.module.params.get('tmp_root')
        self.variables = self.module.params.get('variables', {})

        self._has_run, self._errored = False, False
        self.test_result, self.total_tests, self.failed_tests, self.failed_messages = None, None, None, None

        # establish directories and files
        self.bin_dir, self.executable, self.log_dir, self.log_file, self.result_file = \
            os.path.join(self.tmp_root, 'bin'), \
            os.path.join(self.tmp_root, 'bin', 'goss'), \
            os.path.join(self.tmp_root, 'logs'), \
            os.path.join(self.tmp_root, 'logs', 'degoss.log'), \
            os.path.join(self.tmp_root, 'result.json') \

        # now that all independent variables are initialized, call initialization methods
        self.logger = None

        # arch/os detection
        self.os, self.arch = None, None


    def initialize(self):
        """Initialize the module."""
        # create runtime directories
        self.setup_directories()

        if not self.logger:
            self.logger = self.setup_logging()

        # detect platform information
        self.os, self.arch = self.detect_environment()

        self.logger.debug("Detected host operating system (%s) and architecture (%s).", self.os, self.arch)

    def detect_environment(self):
        """Detect the runtime environment on the host."""
        uname = platform.uname()

        current_os, current_arch = uname[0].lower(), uname[4]

        if current_arch == 'x86_64':
            # goss publishes as goss-linux-amd64
            current_arch = 'amd64'
        elif current_arch == 'i386':
            # goss publishes as goss-linux-386
            current_arch = '386'

        return current_os, current_arch

    def setup_logging(self):
        """Setup logging for the module based on parameters."""
        # rewrite warning to warn
        logging.addLevelName(30, 'WARN')

        # configure output handlers
        buffer_handler = logging.StreamHandler(stream=self.log_output)
        buffer_handler.setFormatter(logging.Formatter(CONSOLE_LOGGING_FORMAT))

        logger = logging.getLogger('degoss')

        # catchall handler for saving output
        logger.addHandler(buffer_handler)

        # setup on-disk logging
        disk_handler = logging.FileHandler(filename=self.log_file)
        disk_handler.setFormatter(logging.Formatter(DISK_LOGGING_FORMAT))
        logger.addHandler(disk_handler)

        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)

        # emit logging configuration
        logger.debug("Logging configuration: debug=%s, log_file=%s", self.debug, self.log_file)

        return logger

    def setup_directories(self):
        """Create and manage directories critical to the degoss lifecycle."""
        for directory in [self.bin_dir, self.log_dir]:
            if not os.path.isdir(directory):
                os.makedirs(directory)

                if self.os in ('linux', 'darwin'):
                    os.chmod(directory, 0o0755)

    @property
    def failed(self):
        """Return whether the run failed."""
        return self.has_run and self.failed_tests > 0

    @property
    def passed(self):
        """Return whether the run passed."""
        return self.has_run and not self.failed and not self.errored

    @property
    def errored(self):
        """Return whether the run threw an error."""
        return self._has_run and self._errored

    @property
    def has_run(self):
        """Return whether we have already attempted to run tests."""
        return self._has_run

    @property
    def version(self):
        """Get the version of Goss to download."""
        if not self._version:
            self._version = self.get_latest_version() if self.requested_version == 'latest' else self.requested_version

        return self._version

    def get_latest_version(self):
        """Detect and return the latest available version of Goss."""

        status, url, response = self.request("{}/releases/latest".format(REPO_URL))

        if status != 200:
            self.fail("Unable to determine latest Goss release, HTTP status %d".format(status))

        # url will be something like https://github.com/aelsabbahy/goss/releases/tag/v0.3.6,
        # we will extract the tag from this url, then attempt to transform this into a version
        tag = url.split('/')[-1]

        version = tag[1:] if tag[0] == 'v' else tag

        self.logger.info("Detected latest available Goss version as %s", version)

        return version

    def get_bool(self, name, default=False):
        """Get a booleanish parameter from the module parameters."""
        param = self.module.params.get(name, default)

        if param in (True, False):
            return param
        elif isinstance(param, str):
            return BOOLEAN_TRUE_MATCHER.search(param) is not None
        else:
            return False

    def get_release_url(self):
        """Fetch the Goss binary URL."""
        # regardless, return the release URL
        return "{}/releases/download/v{}/goss-{}-{}".format(REPO_URL, self.version, self.os, self.arch)

    def request(self, url, method='GET'):
        """Make an HTTP request to the given URL and return the response."""

        r = Request(url)
        r.get_method = lambda: method

        response = urlopen(r)
        status, response_url = response.getcode(), response.geturl()

        return status, response_url, response

    def deserialize_dict(self, value):
        """Deserialize a value into a dictionary."""
        if isinstance(value, string_types):
            try:
                # it's a string so try to deserialize it into a JSON dictionary.
                result = json.loads(value)

                if not isinstance(result, dict):
                    raise Exception("String value did not contain a dictionary, rather a {}".format(type(result)))

                return result
            except Exception as e:
                self.logger.error("Unable to deserialize value, using an empty dictionary: %s", e)

                return {}
        elif isinstance(value, dict):
            return value
        else:
            self.logger.error("Input value was neither a string nor a dictionary, rather a {}".format(type(value)))
            return {}

    def execute(self):
        """Run the module."""
        try:
            self.initialize()
            self.install()
            self.test()
        finally:
            self.clean()

        result = {
            'changed': False,
            'failures': self.failed_messages,
            'test_result': self.test_result,
            'tests_failed': self.failed_tests,
            'tests_passed': self.total_tests - self.failed_tests,
            'tests_total': self.total_tests,
        }

        # if we have made it this far, there weren't any execution issues
        if self.failed:
            self.logger.info("Goss test(s) failed, %d of %d test(s) failed: %s%s", self.failed_tests, self.total_tests,
                os.linesep, (os.linesep + os.linesep).join(self.failed_messages))

            result['failed'] = True
            result['msg'] = "Goss Tests Failed"
        else:
            self.logger.info("Goss test(s) successful, no failed tests out of %d total test(s).", self.total_tests)

            result['failed'] = False
            result['msg'] = "Goss Tests Passed"

        self.module.exit_json(**result)

    def install(self):
        """Install the Goss binary."""
        release_url = self.get_release_url()

        self.logger.info("Installing the Goss binary from %s into %s", release_url, self.bin_dir)

        status, _, response = self.request(release_url)

        # write to a file
        with open(self.executable, 'w') as f:
            # buffered read at 8KiB chunks
            chunk = response.read(BUFFER_SIZE)

            while chunk:
                f.write(chunk)
                chunk = response.read(BUFFER_SIZE)

            response.close()

        if self.os in ('linux', 'darwin'):
            # make it executable by the current user
            os.chmod(self.executable, 0o0700)

        self.logger.debug("Successfully installed the binary to %s", self.executable)

    def test(self):
        """Execute the test cases."""
        # deserialize the facts; note that when passing in a dictionary from Ansible as an argument, it is serialized
        # into JSON before passing into the module, therefore we may need to deserialize
        self.logger.debug("Deserializing facts from JSON input")
        self.facts = self.deserialize_dict(self.facts)

        # ansible_facts strips the leading ansible_ prefix from variables, restore it to avoid collisions
        for key in self.facts.keys():
            if not key.startswith("ansible_"):
                self.facts["ansible_{}".format(key)] = self.facts.pop(key)

        self.logger.debug("Deserializing variables from JSON input")
        self.variables = self.deserialize_dict(self.variables)

        # merge variables together
        goss_variables = {}
        goss_variables.update(self.facts)
        goss_variables.update(self.variables)

        self.logger.debug("Variable names exposed to Goss: %s", goss_variables.keys())

        # execute the test cases, piping in variables to standard input to avoid storing them on disk
        self.logger.info("Executing Goss test cases")

        cli_arguments = [self.executable, '--gossfile', self.test_file, '--vars', '/dev/stdin', 'validate',
            '--no-color', '--format', 'json']

        self.logger.debug("Executing Goss as \"%s\" in %s; environment variables: %s", " ".join(cli_arguments),
            self.test_dir, dict(os.environ))

        p = subprocess.Popen(cli_arguments, cwd=self.test_dir, env=dict(os.environ), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

        stdout, _ = p.communicate(input=json.dumps(goss_variables))

        self._has_run = True

        try:
            result = json.loads(stdout)

            self.logger.debug("Writing Goss JSON test results to %s", self.result_file)

            with open(self.result_file, 'w') as f:
                f.write(json.dumps(result, indent=2, sort_keys=True))

            self.logger.debug("Goss executed successfully, looking for failed test cases.")

            self.test_result = result
            self.total_tests = result.get('summary', {}).get('test-count', 0)
            self.failed_tests = result.get('summary', {}).get('failed-count', 0)

            if self.failed_tests > 0:
                self.failed_messages = [
                    case['summary-line'] for case in result['results'] if case['successful'] != True
                ]
        except Exception as e:
            self._errored = True

            self.logger.error("Fatal Goss error (rc=%d): %s", p.returncode, e)
            self.fail("Goss Execution Failed (Unable to run tests) (rc={})".format(p.returncode),
                stdout_lines=stdout.split(os.linesep), rc=p.returncode)

    def clean(self):
        """Clean everything up."""
        if self.do_clean and os.path.exists(self.tmp_root) and os.path.isdir(self.tmp_root):
            if (self.failed or self.errored) and not self.clean_on_failure:
                # when not clean_on_failure and errors/failures encountered, no-op
                self.logger.info("Not cleaning because clean_on_failure is false and there were errors/failures.")
                return

            self.logger.info("Removing all traces of Goss from the system")
            self.logger.debug("Recursively removing the temporary root directory %s", self.tmp_root)
            shutil.rmtree(self.tmp_root)
        elif not self.do_clean:
            self.logger.info("Cleaning is disabled, taking no action to remove %s", self.tmp_root)
        else:
            self.logger.error("Unable to clean up: %s is not a directory on disk", self.tmp_root)

    def fail(self, message, **kwargs):
        """Fail with a message."""
        self.logger.error("Fatal module or Goss execution error: %s", message)

        # clean ALWAYS, no matter what
        try:
            self.clean()
        except Exception as e:
            self.logger.error("Exception raised when trying to clean up: %s", e)

        output_lines = [line for line in self.log_output.getvalue().split(os.linesep) if len(line) > 0]
        self.module.exit_json(failed=True, module_failed=True, msg=message, output_lines=output_lines,
            test_count=self.total_tests, failed_tests=self.failed_tests, **kwargs)


if __name__ == "__main__":
    main()
