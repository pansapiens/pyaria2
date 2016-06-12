'''The MIT License (MIT)

Copyright (c) 2014 Killua

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Description: pyaria2 is a Python 2/3 module that provides a wrapper class around Aria2's RPC interface. It can be used to build applications that use Aria2 for downloading data.
Author: Killua
Email: killua_hzl@163.com
'''

# !/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess

import xmlrpc.client as xmlrpclib
import os
import time

from string import ascii_letters
from random import choice

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 6800
SERVER_URI_FORMAT = 'http://{}:{:d}/rpc'

UPPER_PORT_LIMIT = 65535
LOWER_PORT_LIMIT = 1024


class PyAria2(object):
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, session=None,
                 rpc_secret=None, max_connections=20, max_downloads=1,
                 max_download_speed="200K", download_dir=None):
        '''
        PyAria2 constructor.

        host: string, aria2 rpc host, default is 'localhost'
        port: integer, aria2 rpc port, default is 6800
        session: string, aria2 rpc session saving.
        '''
        if not PyAria2.LOWER_PORT_LIMIT <= port <= PyAria2.UPPER_PORT_LIMIT:
            raise Exception(
                "port is not between {0} and {1}".format(PyAria2.LOWER_PORT_LIMIT, PyAria2.UPPER_PORT_LIMIT)
            )

        if rpc_secret is not None:
            self.useSecret = True
            self.rpcSecret = rpc_secret
        else:
            self.useSecret = False
            self.rpcSecret = None

        if not isAria2Installed():
            raise Exception('aria2 is not installed, please install it before.')

        settings = {
            "port": port,
            "max_downloads": max_downloads,
            "max_connections": max_connections,
            "max_download_speed": max_download_speed,
        }

        if download_dir is not None:
            settings["download_dir"] = download_dir

        server_uri = SERVER_URI_FORMAT.format(host, port)
        self.server = xmlrpclib.ServerProxy(server_uri, allow_none=True)

        if not isAria2rpcRunning():
            self.start_aria_server(session, settings)
        else:
            pass  # print('aria2 RPC server is already running.')

    def start_aria_server(self, session, settings):
        cmd = 'aria2c' \
              ' --enable-rpc' \
              ' --rpc-listen-port %(port)d' \
              ' --continue' \
              ' --max-concurrent-downloads=%(max_downloads)s' \
              ' --max-connection-per-server=%(max_connections)' \
              ' --max-download-limit=%(max_download_speed)' \
              ' --dir=%(download_dir)s' \
              ' --rpc-max-request-size=1024M' % settings

        if self.useSecret:
            cmd += " --rpc-secret=%s" % self.rpcSecret

        if not session is None:
            cmd += ' --input-file=%s' \
                   ' --save-session-interval=60' \
                   ' --save-session=%s' % (session, session)

        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        count = 0

        while True:
            if isAria2rpcRunning():
                break
            else:
                count += 1
                time.sleep(3)
            if count == 10:
                raise Exception('aria2 RPC server started failure.')

        print('aria2 RPC server is started.')

    def generateSecret(self):
        def gimmeLetters(how_many):
            for i in range(how_many):
                yield choice(ascii_letters)

        return "".join(gimmeLetters(15))

    def fixOptions(self, options):
        return options or dict()

    def fixUris(self, uris):
        return uris or list()

    def addUri(self, uris, options=None, position=None):
        '''
        This method adds new HTTP(S)/FTP/BitTorrent Magnet URI.

        uris: list, list of URIs
        options: dict, additional options
        position: integer, position in download queue

        return: This method returns GID of registered download.
        '''
        uris, options = self.fixUris(uris), self.fixOptions(options)
        if self.useSecret:
            return self.server.aria2.addUri("token:" + self.rpcSecret, uris, options, position)
        else:
            return self.server.aria2.addUri(uris, options, position)

    def addTorrent(self, torrent, uris=None, options=None, position=None):
        '''
        This method adds BitTorrent download by uploading ".torrent" file.

        torrent: string, torrent file path
        uris: list, list of webseed URIs
        options: dict, additional options
        position: integer, position in download queue

        return: This method returns GID of registered download.
        '''
        uris, options = self.fixUris(uris), self.fixOptions(options)
        with open(torrent, "rb") as torrentfile:
            content = torrentfile.read()
            binaryContent = xmlrpclib.Binary(content)
            if self.useSecret:
                fixedSecretPhrase = "token:{}".format(self.rpcSecret)
                return self.server.aria2.addTorrent(fixedSecretPhrase, binaryContent, uris, options, position)
            else:
                return self.server.aria2.addTorrent(binaryContent, uris, options, position)

    def addMetalink(self, metalink, options=None, position=None):
        '''
        This method adds Metalink download by uploading ".metalink" file.

        metalink: string, metalink file path
        options: dict, additional options
        position: integer, position in download queue

        return: This method returns list of GID of registered download.
        '''
        options = self.fixOptions(options)
        if self.useSecret:
            return self.server.aria2.addMetalink("token:" + self.rpcSecret,
                                                 xmlrpclib.Binary(open(metalink, 'rb').read()), options, position)
        else:
            return self.server.aria2.addMetalink(xmlrpclib.Binary(open(metalink, 'rb').read()), options, position)

    def remove(self, gid):
        '''
        This method removes the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of removed download.
        '''

        if self.useSecret:
            return self.server.aria2.remove("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.remove(gid)

    def forceRemove(self, gid):
        '''
        This method removes the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of removed download.
        '''

        if self.useSecret:
            return self.server.aria2.forceRemove("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.forceRemove(gid)

    def pause(self, gid):
        '''
        This method pauses the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of paused download.
        '''

        if self.useSecret:
            return self.server.aria2.pause("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.pause(gid)

    def pauseAll(self):
        '''
        This method is equal to calling aria2.pause() for every active/waiting download.

        return: This method returns OK for success.
        '''

        if self.useSecret:
            return self.server.aria2.pauseAll("token:" + self.rpcSecret)
        else:
            return self.server.aria2.pauseAll()

    def forcePause(self, gid):
        '''
        This method pauses the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of paused download.
        '''

        if self.useSecret:
            return self.server.aria2.forcePause("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.forcePause(gid)

    def forcePauseAll(self):
        '''
        This method is equal to calling aria2.forcePause() for every active/waiting download.

        return: This method returns OK for success.
        '''

        if self.useSecret:
            return self.server.aria2.forcePauseAll("token:" + self.rpcSecret)
        else:
            return self.server.aria2.forcePauseAll()

    def unpause(self, gid):
        '''
        This method changes the status of the download denoted by gid from paused to waiting.

        gid: string, GID.

        return: This method returns GID of unpaused download.
        '''

        if self.useSecret:
            return self.server.aria2.unpause("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.unpause(gid)

    def unpauseAll(self):
        '''
        This method is equal to calling aria2.unpause() for every active/waiting download.

        return: This method returns OK for success.
        '''

        if self.useSecret:
            return self.server.aria2.unpauseAll("token:" + self.rpcSecret)
        else:
            return self.server.aria2.unpauseAll()

    def tellStatus(self, gid, keys=None):
        '''
        This method returns download progress of the download denoted by gid.

        gid: string, GID.
        keys: list, keys for method response.

        return: The method response is of type dict and it contains following keys.
        '''

        if self.useSecret:
            return self.server.aria2.tellStatus("token:" + self.rpcSecret, gid, keys)
        else:
            return self.server.aria2.tellStatus(gid, keys)

    def getUris(self, gid):
        '''
        This method returns URIs used in the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''

        if self.useSecret:
            return self.server.aria2.getUris("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.getUris(gid)

    def getFiles(self, gid):
        '''
        This method returns file list of the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''

        if self.useSecret:
            return self.server.aria2.getFiles("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.getFiles(gid)

    def getPeers(self, gid):
        '''
        This method returns peer list of the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''

        if self.useSecret:
            return self.server.aria2.getPeers("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.getPeers(gid)

    def getServers(self, gid):
        '''
        This method returns currently connected HTTP(S)/FTP servers of the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''

        if self.useSecret:
            return self.server.aria2.getServers("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.getServers(gid)

    def tellActive(self, keys=None):
        '''
        This method returns the list of active downloads.

        keys: keys for method response.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''

        if self.useSecret:
            return self.server.aria2.tellActive("token:" + self.rpcSecret, keys)
        else:
            return self.server.aria2.tellActive(keys)

    def tellWaiting(self, offset, num, keys=None):
        '''
        This method returns the list of waiting download, including paused downloads.

        offset: integer, the offset from the download waiting at the front.
        num: integer, the number of downloads to be returned.
        keys: keys for method response.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''

        if self.useSecret:
            return self.server.aria2.tellWaiting("token:" + self.rpcSecret, offset, num, keys)
        else:
            return self.server.aria2.tellWaiting(offset, num, keys)

    def tellStopped(self, offset, num, keys=None):
        '''
        This method returns the list of stopped download.

        offset: integer, the offset from the download waiting at the front.
        num: integer, the number of downloads to be returned.
        keys: keys for method response.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''

        if self.useSecret:
            return self.server.aria2.tellStopped("token:" + self.rpcSecret, offset, num, keys)
        else:
            return self.server.aria2.tellStopped(offset, num, keys)

    def changePosition(self, gid, pos, how):
        '''
        This method changes the position of the download denoted by gid.

        gid: string, GID.
        pos: integer, the position relative which to be changed.
        how: string.
             POS_SET, it moves the download to a position relative to the beginning of the queue.
             POS_CUR, it moves the download to a position relative to the current position.
             POS_END, it moves the download to a position relative to the end of the queue.

        return: The response is of type integer and it is the destination position.
        '''

        if self.useSecret:
            return self.server.aria2.changePosition("token:" + self.rpcSecret, gid, pos, how)
        else:
            return self.server.aria2.changePosition(gid, pos, how)

    def changeUri(self, gid, fileIndex, delUris, addUris, position=None):
        '''
        This method removes URIs in delUris from and appends URIs in addUris to download denoted by gid.

        gid: string, GID.
        fileIndex: integer, file to affect (1-based)
        delUris: list, URIs to be removed
        addUris: list, URIs to be added
        position: integer, where URIs are inserted, after URIs have been removed

        return: This method returns a list which contains 2 integers. The first integer is the number of URIs deleted. The second integer is the number of URIs added.
        '''

        if self.useSecret:
            return self.server.aria2.changeUri("token:" + self.rpcSecret, gid, fileIndex, delUris, addUris, position)
        else:
            return self.server.aria2.changeUri(gid, fileIndex, delUris, addUris, position)

    def getOption(self, gid):
        '''
        This method returns options of the download denoted by gid.

        gid: string, GID.

        return: The response is of type dict.
        '''

        if self.useSecret:
            return self.server.aria2.getOption("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.getOption(gid)

    def changeOption(self, gid, options):
        '''
        This method changes options of the download denoted by gid dynamically.

        gid: string, GID.
        options: dict, the options.

        return: This method returns OK for success.
        '''

        if self.useSecret:
            return self.server.aria2.changeOption("token:" + self.rpcSecret, gid, options)
        else:
            return self.server.aria2.changeOption(gid, options)

    def getGlobalOption(self):
        '''
        This method returns global options.

        return: The method response is of type dict.
        '''

        if self.useSecret:
            return self.server.aria2.getGlobalOption("token:" + self.rpcSecret)
        else:
            return self.server.aria2.getGlobalOption()

    def changeGlobalOption(self, options):
        '''
        This method changes global options dynamically.

        options: dict, the options.

        return: This method returns OK for success.
        '''

        if self.useSecret:
            return self.server.aria2.changeGlobalOption("token:" + self.rpcSecret, options)
        else:
            return self.server.aria2.changeGlobalOption(options)

    def getGlobalStat(self):
        '''
        This method returns global statistics such as overall download and upload speed.

        return: The method response is of type struct and contains following keys.
        '''

        if self.useSecret:
            return self.server.aria2.getGlobalStat("token:" + self.rpcSecret)
        else:
            return self.server.aria2.getGlobalStat()

    def purgeDownloadResult(self):
        '''
        This method purges completed/error/removed downloads to free memory.

        return: This method returns OK for success.
        '''

        if self.useSecret:
            return self.server.aria2.purgeDownloadResult("token:" + self.rpcSecret)
        else:
            return self.server.aria2.purgeDownloadResult()

    def removeDownloadResult(self, gid):
        '''
        This method removes completed/error/removed download denoted by gid from memory.

        return: This method returns OK for success.
        '''

        if self.useSecret:
            return self.server.aria2.removeDownloadResult("token:" + self.rpcSecret, gid)
        else:
            return self.server.aria2.removeDownloadResult(gid)

    def getVersion(self):
        '''
        This method returns version of the program and the list of enabled features.

        return: The method response is of type dict and contains following keys.
        '''

        if self.useSecret:
            return self.server.aria2.getVersion("token:" + self.rpcSecret)
        else:
            return self.server.aria2.getVersion()

    def getSessionInfo(self):
        '''
        This method returns session information.

        return: The response is of type dict.
        '''

        if self.useSecret:
            return self.server.aria2.getSessionInfo("token:" + self.rpcSecret)
        else:
            return self.server.aria2.getSessionInfo()

    def shutdown(self):
        '''
        This method shutdowns aria2.

        return: This method returns OK for success.
        '''

        if self.useSecret:
            return self.server.aria2.shutdown("token:" + self.rpcSecret)
        else:
            return self.server.aria2.shutdown()

    def forceShutdown(self):
        '''
        This method shutdowns aria2.

        return: This method returns OK for success.
        '''

        if self.useSecret:
            return self.server.aria2.forceShutdown("token:" + self.rpcSecret)
        else:
            return self.server.aria2.forceShutdown()


def isAria2Installed():
    for cmdpath in os.environ['PATH'].split(':'):
        if os.path.isdir(cmdpath) and 'aria2c' in os.listdir(cmdpath):
            return True

    return False


def isAria2rpcRunning():
    pgrep_process = subprocess.Popen('pgrep -l aria2', shell=True, stdout=subprocess.PIPE)

    if pgrep_process.stdout.readline() == b'':
        return False
    else:
        return True
