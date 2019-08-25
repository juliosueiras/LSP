from .process import get_server_working_directory_and_ensure_existence
from .process import start_server
from .process import add_extension_if_missing
from .test_session import test_config
from unittest import TestCase
from os.path import split
from copy import deepcopy
import os


class ProcessModuleTest(TestCase):

    def test_add_extension_if_missing(self):
        if os.name != "nt":
            self.skipTest("only useful for windows")
        # TODO: More extensive tests.
        args = add_extension_if_missing(["cmd"])
        self.assertListEqual(args, ["cmd"])

    def test_get_server_working_directory_and_ensure_existence(self):
        cwd = get_server_working_directory_and_ensure_existence(test_config)
        cwd, leaf = split(cwd)
        self.assertEqual(leaf, "test")
        cwd, leaf = split(cwd)
        self.assertEqual(leaf, "LSP")

    def test_start_server_failure(self):
        config = deepcopy(test_config)
        config.binary_args = ["some_file_that_most_definitely_does_not_exist", "a", "b", "c"]
        with self.assertRaises(FileNotFoundError):
            start_server(config, {}, False)

    def test_start_server(self):
        config = deepcopy(test_config)  # Don't modify the original dict.
        if os.name == "nt":
            config.binary_args = ["cmd.exe"]
        else:
            config.binary_args = ["ls"]
        config.binary_args.extend(["a", "b", "c"])
        popen = start_server(config, {}, False)
        self.assertIsNotNone(popen)
        assert popen
        self.assertListEqual(popen.args[1:], ["a", "b", "c"])
