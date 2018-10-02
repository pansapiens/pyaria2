import unittest

from pyaria2 import PyAria2
from random import choice
from time import sleep
import os
import shutil

ENABLE_LONG_TESTS = False
ENABLE_VERY_LONG_TESTS = False


def setUpModule():
    try:
        os.mkdir("tests/trash")
    except OSError:
        pass


def tearDownModule():
    shutil.rmtree("tests/trash")


class Aria2TestCase(unittest.TestCase):
    def setUp(self):
        self.known_ports = [1025, 1026, 1027]
        self.insecure_aria = PyAria2('localhost', self.known_ports[0])
        self.secure_aria = PyAria2('localhost', self.known_ports[1],
                                   rpcSecret={"useSecret": True, "secret": "welovemiyuki"})

    # def tearDown(self):
    #     self.insecure_aria.shutdown()
    #     self.secure_aria.shutdown()


class TestRunningAria(Aria2TestCase):
    def test_constrainedPortNumber(self):
        # we just test > 65535 and < 1024: we have a lot of testing for correct ports :D
        self.assertRaises(AssertionError, PyAria2, ('localhost',), port=50)
        self.assertRaises(AssertionError, PyAria2, ('localhost',), port=100000)
        self.assertRaises(AssertionError, PyAria2, ('localhost',), port=50,
                          rpcSecret={"useSecret": True, "secret": "mfw"})
        self.assertRaises(AssertionError, PyAria2, ('localhost',), port=100000,
                          rpcSecret={"useSecret": True, "secret": "mfw"})

    @unittest.skipUnless(ENABLE_VERY_LONG_TESTS, True)
    def test_isRunning(self):
        def test_it(ariaObj):
            self.assertEqual(ariaObj.isAria2rpcRunning(), True)
            ariaObj.forceShutdown()
            sleep(3)
            self.assertEqual(ariaObj.isAria2rpcRunning(), False)

        test_it(PyAria2("localhost", self.known_ports[2]))
        test_it(PyAria2("localhost", self.known_ports[2],
                        rpcSecret={"useSecret": True, "secret": "asagiaqt"}))


class TestUri(Aria2TestCase):
    def perform_UriAdditionWithFolder(self, ariaObj, uri):
        return ariaObj.addUri((uri,), options={"dir": "tests/trash"})

    def test_addUriWithFolder(self):
        # FIXME: set big downloads here, we'll have the time to check active data!
        URI = ["http://alfa.moe/sc/0fh17b5", "http://alfa.moe/sc/pn2hzaj"]
        self.perform_UriAdditionWithFolder(self.insecure_aria, URI[0])
        self.perform_UriAdditionWithFolder(self.secure_aria, URI[1])


class TestTorrent(Aria2TestCase):
    def perform_TorrentAdditionWithFolder(self, ariaObj, torrent):
        ariaObj.addTorrent(torrent, options={"dir": "tests/trash"})

    def test_addTorrentWithFolder(self):
        # FIXME: download these torrents via aria objects w
        URI = ["./tests/with_torrents/nisemono.torrent"] * 2
        self.perform_TorrentAdditionWithFolder(self.insecure_aria, URI[0])
        self.perform_TorrentAdditionWithFolder(self.secure_aria, URI[1])
