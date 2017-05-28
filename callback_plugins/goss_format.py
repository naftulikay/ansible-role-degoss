#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from ansible import constants as C
from ansible.plugins.callback import CallbackBase

import json


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'goss_format'

    def print_goss_output(self, result, output_format):
        for output in ('stdout', 'stderr'):
            value = result.get(output, '')

            if len(value) == 0:
                # idgaf
                continue

            if output_format == "json":
                try:
                    value = json.dumps(json.loads(value), indent=2)
                except:
                    pass

            if output_format == "rspecish":
                # offer a newline
                value = "\n{}".format(value)

            self._display.display(value, color=C.COLOR_ERROR)

    def failure_funnel(self, result):
        if not result.is_failed():
            # do. not. care.
            return

        task = result._task
        loader = task._loader if task else None
        host = result._host
        role = task._role
        play = role._play if role else None
        vm = task._variable_manager

        if 'format_goss_output' in task.tags:
            # we have caught us a marlin
            facts = vm.get_vars(loader=loader, task=task, host=host, play=play) if vm else {}
            self.print_goss_output(facts.get('goss_output', {}), facts.get('goss_output_format', 'rspecish'))

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.failure_funnel(result)
        # debug_during_failure("goss_format.py: CallbackModule.v2_runner_on_failed", result)

    def v2_runner_item_on_failed(self, result, ignore_errors=False):
        self.failure_funnel(result)
        # debug_during_failure("goss_format.py: CallbackModule.v2_runner_item_on_failed", result)
