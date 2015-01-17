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

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
try:
    import xmlrpc.client as xmlrpclib
except ImportError:
    import xmlrpclib
import os
import time
from string import letters
from random import choice

class PyAria2(object):
    SERVER_URI_FORMAT = 'http://{}:{:d}/rpc'

    def __init__(self, host='localhost', port=6800, session=None,
                        rpcSecret=None, checkInstallation=False):
        '''
        PyAria2 constructor.

        host: string, aria2 rpc host, default is 'localhost'
        port: integer, aria2 rpc port, default is 6800
        session: string, aria2 rpc session saving.
        '''
        self.host = host
        self.port = port
        self.session = session
        if rpcSecret:
            self.useSecret =  rpcSecret["useSecret"]
            self.fixedSecret = rpcSecret["fixedSecret"]
        else:
            self.useSecret = False
            self.fixedSecret = None

        #I don't really give a **** if it's not installed
        # it will just break and **** $$$ the world.
        if checkInstallation and not isAria2Installed():
            raise Exception('aria2 is not installed, please install it before.')

        if not isAria2rpcRunning():
            cmd = 'aria2c' \
                  ' --enable-rpc' \
                  ' --rpc-listen-port %d' \
                  ' --continue' \
                  ' --max-concurrent-downloads=20' \
                  ' --max-connection-per-server=10' \
                  ' --rpc-max-request-size=1024M' % port

            if rpcSecret and self.useSecret:
                self.fixedSecret = (self.fixedSecret or self.generateSecret())
                cmd += " --rpc-secret=%s" % self.fixedSecret
                self.fixedSecret = "token:"+self.fixedSecret

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
                if count == 5:
                    raise Exception('aria2 RPC server started failure.')
            print('aria2 RPC server is started.')
        else:
            print('aria2 RPC server is already running.')

        server_uri = PyAria2.SERVER_URI_FORMAT.format(host, port)
        self.server = xmlrpclib.ServerProxy(server_uri, allow_none=True)

    def generateSecret(self):
        def gimmeLetters(how_many):
            for i in range(how_many):
                yield choice(letters)
        return "".join(gimmeLetters(15))

    def addUri(self, uris, options=None, position=None):
        '''
        This method adds new HTTP(S)/FTP/BitTorrent Magnet URI.

        uris: list, list of URIs
        options: dict, additional options
        position: integer, position in download queue

        return: This method returns GID of registered download.
        '''
        if self.useSecret:
            return self.server.aria2.addUri(self.fixedSecret, self.fixedSecret, uris, options, position)
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
        
        if self.useSecret:
            return self.server.aria2.addTorrent(self.fixedSecret, xmlrpclib.Binary(open(torrent, 'rb').read()), uris, options, position)
        else:
            return self.server.aria2.addTorrent(xmlrpclib.Binary(open(torrent, 'rb').read()), uris, options, position)
    

    def addMetalink(self, metalink, options=None, position=None):
        '''
        This method adds Metalink download by uploading ".metalink" file.

        metalink: string, metalink file path
        options: dict, additional options
        position: integer, position in download queue

        return: This method returns list of GID of registered download.
        '''
        
        if self.useSecret:
            return self.server.aria2.addMetalink(self.fixedSecret, xmlrpclib.Binary(open(metalink, 'rb').read()), options, position)
        else:
            return self.server.aria2.addMetalink(xmlrpclib.Binary(open(metalink, 'rb').read()), options, position)
    

    def remove(self, gid):
        '''
        This method removes the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of removed download.
        '''
        
        if self.useSecret:
            return self.server.aria2.remove(self.fixedSecret, gid)
        else:
            return self.server.aria2.remove(gid)
    

    def forceRemove(self, gid):
        '''
        This method removes the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of removed download.
        '''
        
        if self.useSecret:
            return self.server.aria2.forceRemove(self.fixedSecret, gid)
        else:
            return self.server.aria2.forceRemove(gid)
    

    def pause(self, gid):
        '''
        This method pauses the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of paused download.
        '''
        
        if self.useSecret:
            return self.server.aria2.pause(self.fixedSecret, gid)
        else:
            return self.server.aria2.pause(gid)
    

    def pauseAll(self):
        '''
        This method is equal to calling aria2.pause() for every active/waiting download.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.pauseAll(self.fixedSecret)
        else:
            return self.server.aria2.pauseAll()
    

    def forcePause(self, gid):
        '''
        This method pauses the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of paused download.
        '''
        
        if self.useSecret:
            return self.server.aria2.forcePause(self.fixedSecret, gid)
        else:
            return self.server.aria2.forcePause(gid)
    

    def forcePauseAll(self):
        '''
        This method is equal to calling aria2.forcePause() for every active/waiting download.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.forcePauseAll(self.fixedSecret)
        else:
            return self.server.aria2.forcePauseAll()
    

    def unpause(self, gid):
        '''
        This method changes the status of the download denoted by gid from paused to waiting.

        gid: string, GID.

        return: This method returns GID of unpaused download.
        '''
        
        if self.useSecret:
            return self.server.aria2.unpause(self.fixedSecret, gid)
        else:
            return self.server.aria2.unpause(gid)
    

    def unpauseAll(self):
        '''
        This method is equal to calling aria2.unpause() for every active/waiting download.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.unpauseAll(self.fixedSecret)
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
            return self.server.aria2.tellStatus(self.fixedSecret, gid, keys)
        else:
            return self.server.aria2.tellStatus(gid, keys)
    

    def getUris(self, gid):
        '''
        This method returns URIs used in the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getUris(self.fixedSecret, gid)
        else:
            return self.server.aria2.getUris(gid)
    

    def getFiles(self, gid):
        '''
        This method returns file list of the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getFiles(self.fixedSecret, gid)
        else:
            return self.server.aria2.getFiles(gid)
    

    def getPeers(self, gid):
        '''
        This method returns peer list of the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getPeers(self.fixedSecret, gid)
        else:
            return self.server.aria2.getPeers(gid)
    

    def getServers(self, gid):
        '''
        This method returns currently connected HTTP(S)/FTP servers of the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getServers(self.fixedSecret, gid)
        else:
            return self.server.aria2.getServers(gid)
    

    def tellActive(self, keys=None):
        '''
        This method returns the list of active downloads.

        keys: keys for method response.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.tellActive(self.fixedSecret, keys)
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
            return self.server.aria2.tellWaiting(self.fixedSecret, offset, num, keys)
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
            return self.server.aria2.tellStopped(self.fixedSecret, offset, num, keys)
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
            return self.server.aria2.changePosition(self.fixedSecret, gid, pos, how)
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
            return self.server.aria2.changeUri(self.fixedSecret, gid, fileIndex, delUris, addUris, position)
        else:
            return self.server.aria2.changeUri(gid, fileIndex, delUris, addUris, position)
    

    def getOption(self, gid):
        '''
        This method returns options of the download denoted by gid.

        gid: string, GID.

        return: The response is of type dict.
        '''
        
        if self.useSecret:
            return self.server.aria2.getOption(self.fixedSecret, gid)
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
            return self.server.aria2.changeOption(self.fixedSecret, gid, options)
        else:
            return self.server.aria2.changeOption(gid, options)
    

    def getGlobalOption(self):
        '''
        This method returns global options.

        return: The method response is of type dict.
        '''
        
        if self.useSecret:
            return self.server.aria2.getGlobalOption(self.fixedSecret)
        else:
            return self.server.aria2.getGlobalOption()
    

    def changeGlobalOption(self, options):
        '''
        This method changes global options dynamically.

        options: dict, the options.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.changeGlobalOption(self.fixedSecret, options)
        else:
            return self.server.aria2.changeGlobalOption(options)
    

    def getGlobalStat(self):
        '''
        This method returns global statistics such as overall download and upload speed.

        return: The method response is of type struct and contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getGlobalStat(self.fixedSecret)
        else:
            return self.server.aria2.getGlobalStat()
    

    def purgeDownloadResult(self):
        '''
        This method purges completed/error/removed downloads to free memory.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.purgeDownloadResult(self.fixedSecret)
        else:
            return self.server.aria2.purgeDownloadResult()
    

    def removeDownloadResult(self, gid):
        '''
        This method removes completed/error/removed download denoted by gid from memory.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.removeDownloadResult(self.fixedSecret, gid)
        else:
            return self.server.aria2.removeDownloadResult(gid)
    

    def getVersion(self):
        '''
        This method returns version of the program and the list of enabled features.

        return: The method response is of type dict and contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getVersion(self.fixedSecret)
        else:
            return self.server.aria2.getVersion()
    

    def getSessionInfo(self):
        '''
        This method returns session information.

        return: The response is of type dict.
        '''
        
        if self.useSecret:
            return self.server.aria2.getSessionInfo(self.fixedSecret)
        else:
            return self.server.aria2.getSessionInfo()
    

    def shutdown(self):
        '''
        This method shutdowns aria2.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.shutdown(self.fixedSecret)
        else:
            return self.server.aria2.shutdown()
    

    def forceShutdown(self):
        '''
        This method shutdowns aria2.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.forceShutdown(self.fixedSecret)
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

