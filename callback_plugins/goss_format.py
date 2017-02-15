#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from ansible import constants as C
from ansible.plugins.callback import CallbackBase

import json
import re


PROLLY_JSON = re.compile(r'^[\{\[]', re.I)


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'goss_format'

    def print_goss_output(self, result):
        result = result._result

        # insert newline
        print()

        for output in ('stdout', 'stderr',):
            value = result.get(output, '')

            if PROLLY_JSON.search(value):
                try:
                    self._display.display(json.dumps(json.loads(value), indent=2), color=C.COLOR_ERROR)
                except:
                    self._display.display(value, color=C.COLOR_ERROR)
            else:
                self._display.display(value, color=C.COLOR_ERROR)

    def v2_runner_item_on_failed(self, result, ignore_errors=False):
        # import pdb ; pdb.set_trace()

        if result._result.get('invocation', {}).get('module_name') == 'goss':
            self.print_goss_output(result)
