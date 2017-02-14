#!/usr/bin/env python

from __future__ import print_function

from ansible.plugins.callback import CallbackBase

import json
import re


PROLLY_JSON = re.compile(r'^[\{\[]', re.I)


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'goss_format'

    def print_goss_output(self, result):
        ansible_result = result
        result = ansible_result._result

        for output in ('stdout', 'stderr',):
            value = result.get(output, '')

            if PROLLY_JSON.search(value):
                try:
                    print(json.dumps(json.loads(value), indent=2))
                except:
                    print(value)
            else:
                print(value)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if result._result.get('invocation', {}).get('module_name') == 'goss':
            self.print_goss_output(result)
