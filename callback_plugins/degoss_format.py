#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from ansible import constants as C
from ansible.plugins.callback import CallbackBase

import json
import os

class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 3.0
    CALLBACK_NAME = 'degoss_format'
    CALLBACK_NEEDS_WHITELIST = False

    def pretty_print(self, task_result):
        """Pretty-print output for a Goss run."""

        result = task_result._result
        output = os.linesep + result.get('msg')

        # note: it seems that Ansible strips out the 'failed' key from the task result outside of our control

        # if tests_failed is null, this means that no tests were actually executed
        module_failed = result.get('module_failed', False)

        # tests can only fail when the module did not fail, so make sure it didn't fail and then count the failures
        tests_failed = not module_failed and result.get('tests_failed', 0) > 0

        # if either the module failed or tests failed, indicate failure
        failed = module_failed or tests_failed

        if module_failed:
            # the module failed, so append the output of the Goss execution
            output += os.linesep + os.linesep.join(map(lambda l: (' ' * 2) + l, result.get('stdout_lines')))

        if tests_failed:
            # goss module execution succeeded, but tests failed
            output += (os.linesep * 2) + (os.linesep * 2).join(result.get('failures'))

        if not module_failed:
            # add a footer that shows all the stats
            # one lulzy thing is that Goss does not have a way to skip tests so we hardcode to zero
            output += (os.linesep * 2) + "(Count: {}, Failed: {}, Skipped: {})".format(
                result.get('tests_total'), result.get('tests_failed'), 0)

        # insert a trailing newline for when running against multiple hosts
        output += os.linesep

        # emit output when successful or failed in the appropriate color
        self._display.display(output, color=C.COLOR_ERROR if failed else C.COLOR_OK)

    def funnel(self, task_result):
        """
        Central ingress point for tasks and formatted output.

        Args:
            task_result: A ansible.executor.task_result.TaskResult for the current task that ran.
        """
        if task_result._task.action == 'degoss':
            try:
                self.pretty_print(task_result)
            except Exception as e:
                raise e

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.funnel(result)

    def v2_runner_item_on_failed(self, result, ignore_errors=False):
        self.funnel(result)

    def v2_runner_on_ok(self, result, ignore_errors=False):
        self.funnel(result)
