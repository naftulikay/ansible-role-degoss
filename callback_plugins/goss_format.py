#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from ansible import constants as C
from ansible.plugins.callback import CallbackBase

import json


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'goss_format'
    CALLBACK_NEEDS_WHITELIST = False

    def print_goss_output(self, result, output_format, error=True):
        """Pretty-print output for a Goss run."""
        for output in ('stdout', 'stderr'):
            value = result.get(output, '')

            if len(value) == 0:
                # idgaf
                continue

            if output_format == "json":
                try:
                    value = json.dumps(json.loads(value), indent=2)
                except:
                    value = "\n{}".format(value.strip())
            else:
                # offer a newline
                value = "\n{}".format(value.strip())

            self._display.display(value, color=C.COLOR_ERROR if error else C.COLOR_OK)

    def print_python_stacktrace(self, exception):
        """Pretty print a Python stacktrace for the failed module call."""
        self._display.display("\n{}".format(str(exception)), color=C.COLOR_ERROR)

    def funnel(self, result):
        """Central ingress point for tasks and formatted output."""
        task = result._task
        loader = task._loader if task else None
        host = result._host
        role = task._role
        play = role._play if role else None
        vm = task._variable_manager
        facts = vm.get_vars(loader=loader, task=task, host=host, play=play) if vm else {}

        goss_output = facts.get('goss_output', {})

        if result.is_failed() and 'format_goss_output' in task.tags:
            # if we had a failure and the task is failed with format_goss_output, errors will be formatted
            self.print_goss_output(goss_output, facts.get('goss_output_format'), error=True)

        if not result.is_failed() and task.action == 'goss' and 'format_goss_output' in task.tags and \
                facts.get('degoss_debug', False):
            # if result is successful, this is a goss run, it has been tagged for formatting, and debug mode is enabled,
            # success will be displayed
            self.print_goss_output(goss_output, facts.get('goss_output_format'), error=False)

        if 'format_goss_stacktrace' in task.tags:
            # if the module failed and there's a stacktrace, print it prettily
            self.print_python_stacktrace(goss_output.get('exception', goss_output.get('module_stderr', "")))

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.funnel(result)

    def v2_runner_item_on_failed(self, result, ignore_errors=False):
        self.funnel(result)

    def v2_runner_on_ok(self, result, ignore_errors=False):
        self.funnel(result)
