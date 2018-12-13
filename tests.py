#!/usr/bin/env python
# -*- coding utf-8 -*-

from callback_plugins.degoss_format import CallbackModule as DegossCallbackModule
from library.degoss import (
    CONSOLE_LOGGING_FORMAT,
    DISK_LOGGING_FORMAT,
    Degoss
)

import json
import logging
import mock
import os
import subprocess
import sys
import unittest

class DegossTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        # call superclass constructor
        super(DegossTestCase, self).__init__(*args, **kwargs)

        self.module, self.service = None, None

    @property
    def __name__(self):
        return "DegossTestCase"

    def setUp(self):
        """Configure fixtures."""
        self.logger = mock.MagicMock()

        self.module = mock.MagicMock()
        self.module.params = {
            # boolean stubs
            'literal_true': True,
            'literal_false': False,
            'string_true_0': 'true',
            'string_true_1': 'True',
            'string_true_2': 'yes',
            'string_true_3': 'on',
            'string_false_0': 'false',
            'string_false_1': 'False',
            'string_false_2': 'no',
            'string_false_3': 'off',
            # actual
            'debug': True,
            'clean': False,
            'clean_on_failure': False,
            'facts': '{ "fact": true }',
            'test_dir':  '/tmp/degoss.demo/tests',
            'test_file': '/tmp/degoss.demo/tests/dingo.yml',
            'tmp_root':  '/tmp/degoss.demo',
            'version': '0.3.6',
        }

        self.service = Degoss(sys.argv, self.module)
        self.service.logger = self.logger
        self.service.os, self.service.arch = 'linux', 'amd64'

    def test_get_boolean(self):
        """Test that boolean resolution works as expected."""
        self.assertTrue(self.service.get_bool('literal_true'))
        self.assertFalse(self.service.get_bool('literal_false'))

        self.assertTrue(self.service.get_bool('string_true_0'))
        self.assertTrue(self.service.get_bool('string_true_1'))
        self.assertTrue(self.service.get_bool('string_true_2'))
        self.assertTrue(self.service.get_bool('string_true_3'))

        self.assertFalse(self.service.get_bool('string_false_0'))
        self.assertFalse(self.service.get_bool('string_false_1'))
        self.assertFalse(self.service.get_bool('string_false_2'))
        self.assertFalse(self.service.get_bool('string_false_3'))

    def test_constructor(self):
        """Tests that the constructor correctly assigns variables from the module input."""
        self.assertEqual(True, self.service.debug)
        self.assertEqual(False, self.service.do_clean)
        self.assertEqual(False, self.service.clean_on_failure)
        self.assertEqual('/tmp/degoss.demo/logs', self.service.log_dir)
        self.assertEqual('/tmp/degoss.demo/logs/degoss.log', self.service.log_file)
        self.assertEqual('/tmp/degoss.demo/bin', self.service.bin_dir)
        self.assertEqual('/tmp/degoss.demo/tests', self.service.test_dir)
        self.assertEqual('dingo.yml', self.service.test_file)
        self.assertEqual('/tmp/degoss.demo', self.service.tmp_root)
        self.assertEqual('0.3.6', self.service.requested_version)

        self.assertIsNotNone(self.service.log_output)

    @mock.patch('library.degoss.platform.uname')
    def test_detect_environment(self, mock_uname):
        """Tests that environment detection works."""
        mock_uname.return_value = ('Linux', None, None, None, 'x86_64')

        detected_os, detected_arch = self.service.detect_environment()

        self.assertEqual('linux', detected_os)
        self.assertEqual('amd64', detected_arch)

        mock_uname.return_value = ('Linux', None, None, None, 'i386')

        self.service = Degoss(sys.argv, self.module)
        detected_os, detected_arch = self.service.detect_environment()

        self.assertEqual('linux', detected_os)
        self.assertEqual('386', detected_arch)

    @mock.patch.object(Degoss, 'version', new_callable=mock.PropertyMock)
    def test_get_release_url(self, mock_version):
        mock_version.return_value = '0.3.6'

        self.service.os = 'linux'
        self.service.arch = 'amd64'

        self.assertEqual("https://github.com/aelsabbahy/goss/releases/download/v0.3.6/goss-linux-amd64",
            self.service.get_release_url())

    @mock.patch.object(Degoss, 'get_latest_version')
    def test_version_latest(self, mock_get_latest_version):
        """Tests the version getter resolves the latest version properly."""
        mock_get_latest_version.return_value = '9.9.9'
        self.module.params['version'] = 'latest'
        self.service = Degoss(sys.argv, self.module)

        self.assertEqual('9.9.9', self.service.version)

    @mock.patch.object(Degoss, 'get_latest_version')
    def test_version_hardcoded(self, mock_get_latest_version):
        """Tests that the version getter returns the specified version."""
        self.assertEqual('0.3.6', self.service.version)
        mock_get_latest_version.assert_not_called()

    def test_failed(self):
        """Tests whether failure detection works as expected."""
        self.service._has_run, self.service.failed_tests = False, 0
        self.assertFalse(self.service.failed)

        self.service._has_run = True
        self.assertFalse(self.service.failed)

        self.service.failed_tests = 1
        self.assertTrue(self.service.failed)

    def test_passed(self):
        """Tests whether success detection works as expected."""
        self.service._has_run = False
        self.assertFalse(self.service.passed)

        self.service._has_run, self.service.failed_tests = False, 0
        self.assertFalse(self.service.passed)

        self.service._has_run = True
        self.assertTrue(self.service.passed)

        self.service.failed_tests = 1
        self.assertFalse(self.service.passed)

    def test_errored(self):
        """Tests whether error detection works as expected."""
        self.service._has_run, self.service._errored = False, False
        self.assertFalse(self.service.errored)

        self.service._has_run = True
        self.assertFalse(self.service.errored)

        self.service._errored = True
        self.assertTrue(self.service.errored)

    def test_has_run(self):
        """Tests whether has_run reflects the execution state."""
        self.service._has_run = False
        self.assertFalse(self.service.has_run)

        self.service._has_run = True
        self.assertTrue(self.service.has_run)

    def test_deserialize_dict(self):
        """Tests that dictionary deserialization works."""
        self.service.logger = mock.MagicMock()

        # edge cases
        self.assertEqual({}, self.service.deserialize_dict(None))
        self.assertEqual({}, self.service.deserialize_dict(''))
        self.assertEqual({}, self.service.deserialize_dict('[]'))

        # main case
        input_value = {
            'a': 1,
            'b': {},
            'c': [],
            'd': {
                'e': 'f'
            }
        }

        self.assertEqual(input_value, self.service.deserialize_dict(json.dumps(input_value)))

    @mock.patch.object(Degoss, 'setup_directories')
    @mock.patch.object(Degoss, 'setup_logging')
    @mock.patch.object(Degoss, 'detect_environment')
    def test_initialize(self, mock_detect_environment, mock_setup_logging, mock_setup_directories):
        """Tests initialization."""
        mock_os, mock_arch = mock.MagicMock(), mock.MagicMock()
        mock_detect_environment.return_value = mock_os, mock_arch

        mock_logger = mock.MagicMock()
        mock_setup_logging.return_value = mock_logger

        self.service = Degoss(sys.argv, self.module)
        self.service.initialize()

        mock_detect_environment.assert_called()
        mock_setup_directories.assert_called()
        mock_setup_logging.assert_called()

        self.assertEqual(mock_arch, self.service.arch)
        self.assertEqual(mock_logger, self.service.logger)
        self.assertEqual(mock_os, self.service.os)

    @mock.patch('library.degoss.logging.FileHandler')
    @mock.patch('library.degoss.logging.StreamHandler')
    @mock.patch('library.degoss.logging.getLogger')
    @mock.patch('library.degoss.logging.addLevelName')
    def test_setup_logging(self, mock_add_level_name, mock_get_logger, mock_new_stream_handler,
            mock_new_file_handler):
        """Tests that logging setup works properly."""
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_file_handler = mock.MagicMock()
        mock_new_file_handler.return_value = mock_file_handler

        mock_stream_handler = mock.MagicMock()
        mock_new_stream_handler.return_value = mock_stream_handler

        self.service = Degoss(sys.argv, self.module)
        logger = self.service.setup_logging()

        # global logging changes
        mock_add_level_name.assert_called_with(30, 'WARN')

        # our logger
        mock_get_logger.assert_called_with('degoss')
        mock_logger.setLevel.assert_called_with(logging.DEBUG)
        mock_logger.addHandler.assert_any_call(mock_file_handler)
        mock_logger.addHandler.assert_any_call(mock_stream_handler)

        # handlers
        mock_new_file_handler.assert_called_with(filename=self.service.log_file)
        mock_new_stream_handler.assert_called_with(stream=self.service.log_output)

        # return value must equal the logger created
        self.assertEqual(mock_logger, logger)

        # test with debug false
        self.module.params['debug'] = False
        self.service = Degoss(sys.argv, self.module)
        self.service.setup_logging()

        mock_logger.setLevel.assert_called_with(logging.INFO)

    @mock.patch('library.degoss.os.chmod')
    @mock.patch('library.degoss.os.makedirs')
    @mock.patch('library.degoss.os.path.isdir')
    def test_setup_directories(self, mock_is_dir, mock_makedirs, mock_chmod):
        """Tests that creation of directories works as expected."""
        mock_is_dir.return_value = False

        self.service.os, self.service.arch = 'linux', 'amd64'
        self.service.setup_directories()

        mock_is_dir.assert_any_call(self.service.bin_dir)
        mock_is_dir.assert_any_call(self.service.log_dir)

        mock_makedirs.assert_any_call(self.service.bin_dir)
        mock_makedirs.assert_any_call(self.service.log_dir)

        mock_chmod.assert_any_call(self.service.bin_dir, 0o0755)
        mock_chmod.assert_any_call(self.service.log_dir, 0o0755)

    @mock.patch('library.degoss.Request')
    @mock.patch('library.degoss.urlopen')
    def test_request(self, mock_urlopen, mock_new_request):
        """Tests that degoss can create URL requests."""
        mock_request = mock.MagicMock()
        mock_new_request.return_value = mock_request

        mock_response = mock.MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = 'redirect'

        mock_urlopen.return_value = mock_response

        status, response_url, response = self.service.request('httpdangus', 'RANG')

        mock_new_request.assert_called_with('httpdangus')
        mock_urlopen.assert_called_with(mock_request)

        self.assertEqual(mock_response, response)
        self.assertEqual(200, status)
        self.assertEqual('redirect', response_url)
        self.assertEqual('RANG', mock_request.get_method())

    @mock.patch.object(Degoss, 'request')
    def test_get_latest_version(self, mock_new_request):
        """Tests that degoss can detect the latest version of Goss from GitHub."""
        mock_request = mock.MagicMock()
        mock_new_request.return_value = 200, 'aelsabbahy/goss/releases/tag/v0.3.6', mock_request

        result = self.service.get_latest_version()

        self.assertEqual('0.3.6', result)
        mock_new_request.assert_called_with("https://github.com/aelsabbahy/goss/releases/latest")

    @mock.patch('library.degoss.os.chmod')
    @mock.patch('library.degoss.open')
    @mock.patch.object(Degoss, 'request')
    @mock.patch.object(Degoss, 'get_release_url')
    def test_install(self, mock_get_release_url, mock_new_request, mock_fopen, mock_chmod):
        """Tests that degoss can install Goss successfully."""
        mock_get_release_url.return_value = 'fhwgads'

        # mock up the response as a file like object
        chunk_status = { 'emitted': False }
        def chunk_once(self):
            if not chunk_status['emitted']:
                chunk_status['emitted'] = True
                return "ABCDEFG"
            else:
                return None

        mock_response = mock.MagicMock()
        mock_response.read = chunk_once
        mock_new_request.return_value = 200, 'url', mock_response

        mock_file = mock.MagicMock()
        mock_file_enterer = mock.MagicMock()
        mock_file_enterer.__enter__.return_value = mock_file
        mock_fopen.return_value = mock_file_enterer

        self.service.install()

        mock_get_release_url.assert_called_with()
        mock_new_request.assert_called_with('fhwgads')

        mock_fopen.assert_called_with(self.service.executable, 'w')
        mock_file.write.assert_called_with('ABCDEFG')

        mock_chmod.assert_called_with(self.service.executable, 0o700)

    @mock.patch('library.degoss.open')
    @mock.patch.object(Degoss, 'fail')
    @mock.patch('library.degoss.subprocess.Popen')
    def test_run_tests_success(self, mock_new_popen, mock_fail, mock_fopen):
        """Tests that degoss can handle successful tests appropriately."""
        result_dict = {
            'summary': {
                'failed-count': 0,
                'test-count': 5,
            }
        }
        result_string = json.dumps(result_dict)

        mock_process = mock.MagicMock()
        mock_process.communicate.return_value = result_string, None
        mock_new_popen.return_value = mock_process

        mock_file = mock.MagicMock()
        mock_file_enterer = mock.MagicMock()
        mock_file_enterer.__enter__.return_value = mock_file
        mock_fopen.return_value = mock_file_enterer

        # create facts and variables as strings to be deserialized
        self.service.facts = json.dumps({
            'fact1': True,
            'fact2': 'yes',
        })

        self.service.variables = json.dumps({
            'var1': ['yup'],
            'var2': None,
        })

        goss_variables = {
            'ansible_fact1': True,
            'ansible_fact2': 'yes',
            'var1': ['yup'],
            'var2': None,
        }

        # run
        self.service.test()

        # a new process should have been opened like this
        mock_new_popen.assert_called_with(
            [self.service.executable, '--gossfile', self.service.test_file, '--vars', '/dev/stdin', 'validate',
                '--no-color', '--format', 'json'],
            cwd=self.service.test_dir,
            env=dict(os.environ),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        # communicate must be called to send variables like this
        mock_process.communicate.assert_called_with(input=json.dumps(goss_variables))

        # it must not have failed
        mock_fail.assert_not_called()
        # it must have opened the result file
        mock_fopen.assert_called_with(self.service.result_file, 'w')
        # it must have written the result to the result file
        mock_file.write.assert_called_with(json.dumps(result_dict, indent=2, sort_keys=True))

        self.assertTrue(self.service._has_run and self.service.has_run)
        self.assertFalse(self.service._errored)
        self.assertFalse(self.service.failed)
        self.assertEqual(0, self.service.failed_tests)
        self.assertEqual(5, self.service.total_tests)
        self.assertEqual(self.service.test_result, result_dict)

    @mock.patch('library.degoss.open')
    @mock.patch.object(Degoss, 'fail')
    @mock.patch('library.degoss.subprocess.Popen')
    def test_run_tests_failure(self, mock_new_popen, mock_fail, mock_fopen):
        """Tests that degoss can handle failed tests appropriately."""
        result_dict = {
            'results': [
                { 'summary-line': "Test execution one failed.", 'successful': False },
                { 'summary-line': "Test execution two failed.", 'successful': False },
                { 'summary-line': "Passed", 'successful': True },
            ],
            'summary': {
                'failed-count': 2,
                'test-count': 5,
            }
        }
        result_string = json.dumps(result_dict)

        mock_process = mock.MagicMock()
        mock_process.communicate.return_value = result_string, None
        mock_new_popen.return_value = mock_process

        mock_file = mock.MagicMock()
        mock_file_enterer = mock.MagicMock()
        mock_file_enterer.__enter__.return_value = mock_file
        mock_fopen.return_value = mock_file_enterer

        self.service.facts, self.service.variables = {}, {}

        # run
        self.service.test()

        # just stubs here, all the logic up until process execution completion is the same

        # process must be creaeted
        mock_new_popen.assert_called()

        # communicate must be passed varialbes
        mock_process.communicate.assert_called_with(input='{}')

        # result file must be written
        mock_file.write.assert_called_with(json.dumps(result_dict, indent=2, sort_keys=True))

        # instance variables
        self.assertEqual(result_dict, self.service.test_result)
        self.assertEqual(2, self.service.failed_tests)
        self.assertEqual(5, self.service.total_tests)
        self.assertEqual([
            "Test execution one failed.",
            "Test execution two failed.",
        ], self.service.failed_messages)

        # it's a failure, but not a critical failue
        mock_fail.assert_not_called()

    @mock.patch('library.degoss.open')
    @mock.patch.object(Degoss, 'fail')
    @mock.patch('library.degoss.subprocess.Popen')
    def test_run_tests_error(self, mock_new_popen, mock_fail, mock_fopen):
        """Tests that degoss can handle error cases when running tests."""
        result_string = "ERROR: some shit didn't work!"

        mock_process = mock.MagicMock()
        mock_process.communicate.return_value = result_string, None
        mock_process.returncode = 1
        mock_new_popen.return_value = mock_process

        mock_file = mock.MagicMock()
        mock_file_enterer = mock.MagicMock()
        mock_file_enterer.__enter__.return_value = mock_file
        mock_fopen.return_value = mock_file_enterer

        self.service.facts, self.service.variables = {}, {}

        # run
        self.service.test()

        mock_new_popen.assert_called()
        mock_process.communicate.assert_called_with(input='{}')
        mock_file.write.assert_not_called()
        mock_fail.assert_called_with("Goss Execution Failed (Unable to run tests) (rc=1)", stdout_lines=[result_string], rc=1 )

        self.assertTrue(self.service._errored)
        self.assertTrue(self.service.errored)


    @mock.patch.object(Degoss, 'errored', new_callable=mock.PropertyMock)
    @mock.patch.object(Degoss, 'failed', new_callable=mock.PropertyMock)
    @mock.patch('library.degoss.os.path.isdir')
    @mock.patch('library.degoss.os.path.exists')
    @mock.patch('library.degoss.shutil.rmtree')
    def test_clean_on_failure(self, mock_rmtree, mock_exists, mock_is_dir, mock_failed, mock_errored):
        """Tests that degoss respects the clean on failure flag appropriately."""
        mock_exists.return_value, mock_is_dir.return_value = True, True

        self.service.clean_on_failure = True
        self.service.do_clean = True
        mock_failed.return_value, mock_errored.return_value = True, True

        # clean: True, clean_on_failure: True, failed: True, errored: True
        self.service.clean()
        mock_rmtree.assert_called_with(self.service.tmp_root)
        mock_rmtree.reset_mock()

        # clean: True, clean_on_failure: False, failed: True, errored: True
        self.service.clean_on_failure = False
        self.service.clean()
        mock_rmtree.assert_not_called()

        # clean: True, clean_on_failure: False, failed: True, errored: False
        mock_failed.return_value, mock_errored.return_value = True, False
        self.service.clean()
        mock_rmtree.assert_not_called()

        # clean: True, clean_on_failure: False, failed: False, errored: True
        mock_failed.return_value, mock_errored.return_value = False, True
        self.service.clean()
        mock_rmtree.assert_not_called()

        # clean: True, clean_on_failure: False, failed: False, errored: False
        mock_failed.return_value, mock_errored.return_value = False, False
        self.service.do_clean = True
        self.service.clean_on_failure = False
        self.service.clean()
        mock_rmtree.assert_called_with(self.service.tmp_root)
        mock_rmtree.reset_mock()

        # clean: True, clean_on_failure: True, failed: True, errored: True
        mock_failed.return_value, mock_errored.return_value = True, True
        self.service.do_clean = True
        self.service.clean_on_failure = True
        self.service.clean()
        mock_rmtree.assert_called_with(self.service.tmp_root)
        mock_rmtree.reset_mock()

        # clean: False, clean_on_failure: True, failed: True, errored: True
        # should supersede clean_on_failure
        self.service.do_clean, self.service.clean_on_failure = False, True
        self.service.clean()
        mock_rmtree.assert_not_called()

    @mock.patch.object(Degoss, 'failed', new_callable=mock.PropertyMock)
    @mock.patch.object(Degoss, 'clean')
    @mock.patch.object(Degoss, 'test')
    @mock.patch.object(Degoss, 'install')
    @mock.patch.object(Degoss, 'initialize')
    def test_execute(self, mock_initialize, mock_install, mock_test, mock_clean, mock_failed):
        """Tests entire workflow execution."""
        self.module.exit_json = mock.MagicMock()

        # test success use case
        mock_failed.return_value = False

        self.service.failed_tests = 0
        self.service.total_tests = 5
        self.service.test_result = { 'time': 'go' }

        self.service.execute()

        mock_initialize.assert_called()
        mock_install.assert_called()
        mock_test.assert_called()
        mock_clean.assert_called()

        self.module.exit_json.assert_called_with(**{
            'changed': False,
            'failed': False,
            'failures': self.service.failed_messages,
            'msg': "Goss Tests Passed",
            'test_result': self.service.test_result,
            'tests_failed': self.service.failed_tests,
            'tests_passed': self.service.total_tests - self.service.failed_tests,
            'tests_total': self.service.total_tests,
        })
        self.module.exit_json.reset_mock()

        # test failure use case
        mock_failed.return_value = True
        self.service.failed_messages = [
            'one failed',
            'two failed',
        ]
        self.service.failed_tests = 2
        self.service.total_tests = 5
        self.service.test_result = { 'oh': 'noes' }

        self.service.execute()

        self.module.exit_json.assert_called_with(**{
            'changed': False,
            'failed': True,
            'failures': self.service.failed_messages,
            'msg': "Goss Tests Failed",
            'test_result': self.service.test_result,
            'tests_failed': self.service.failed_tests,
            'tests_passed': self.service.total_tests - self.service.failed_tests,
            'tests_total': self.service.total_tests,
        })

    @mock.patch.object(Degoss, 'clean')
    def test_fail(self, mock_clean):
        """Tests that fail works as expected."""
        self.module.exit_json = mock.MagicMock()
        self.service.log_output.write("one\n")
        self.service.log_output.write("two\n")

        self.service.fail("Hello", world=True)

        mock_clean.assert_called_with()

        self.module.exit_json.assert_called_with(**{
            'failed': True,
            'failed_tests': None,
            'module_failed': True,
            'msg': "Hello",
            'output_lines': ["one", "two"],
            'test_count': None,
            'world': True,
        })


if __name__ == "__main__":
    unittest.main()
