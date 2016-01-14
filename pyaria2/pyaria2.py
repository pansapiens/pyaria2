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

Patches to make it work with Python2 and add secure XML-RPC communication
Author: alfateam123
Email: alfateam123@nwa.xyz
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
from string import ascii_letters
from random import choice
import socket

class PyAria2(object):
    SERVER_URI_FORMAT = 'http://{}:{:d}/rpc'
    UPPER_PORT_LIMIT = 65535
    LOWER_PORT_LIMIT = 1024

    def __init__(self, host='localhost', port=6800, session=None,
                        rpcSecret=None, checkInstallation=False):
        '''
        PyAria2 constructor.

        host: string, aria2 rpc host, default is 'localhost'
        port: integer, aria2 rpc port, default is 6800
        session: string, aria2 rpc session saving.
        '''
        assert PyAria2.LOWER_PORT_LIMIT <= port <= PyAria2.UPPER_PORT_LIMIT,  \
               "port is not between {0} and {1}".format(PyAria2.LOWER_PORT_LIMIT, PyAria2.UPPER_PORT_LIMIT)
        self.host = host
        self.port = port
        self.session = session
        if rpcSecret:
            self.useSecret =  rpcSecret["useSecret"]
            self.fixedSecret = rpcSecret["secret"]
        else:
            self.useSecret = False
            self.fixedSecret = None

        #I don't really give a **** if it's not installed.
        if checkInstallation and not isAria2Installed():
            raise Exception('aria2 is not installed, please install it before.')

        server_uri = PyAria2.SERVER_URI_FORMAT.format(host, port)
        self.server = xmlrpclib.ServerProxy(server_uri, allow_none=True)

        if not self.isAria2rpcRunning():
            cmd = 'aria2c' \
                  ' --enable-rpc' \
                  ' --rpc-listen-all=true' \
                  ' --rpc-listen-port %d' \
                  ' --continue' \
                  ' --max-concurrent-downloads=20' \
                  ' --max-connection-per-server=10' \
                  ' --rpc-max-request-size=1024M' % port

            if rpcSecret and self.useSecret:
                self.fixedSecret = (self.fixedSecret or self.generateSecret())
                cmd += " --rpc-secret=%s" % self.fixedSecret

            if not session is None:
                cmd += ' --input-file=%s' \
                       ' --save-session-interval=60' \
                       ' --save-session=%s' % (session, session)

            subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    
            count = 0
            while True:
                if self.isAria2rpcRunning():
                    break
                else:
                    count += 1
                    time.sleep(3)
                if count == 5:
                    raise Exception('aria2 RPC server started failure.')
            #print('aria2 RPC server is started.')
        else:
            pass #print('aria2 RPC server is already running.')


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
            return self.server.aria2.addUri("token:"+self.fixedSecret, uris, options, position)
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
                fixedSecretPhrase = "token:{}".format(self.fixedSecret)
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
            return self.server.aria2.addMetalink("token:"+self.fixedSecret, xmlrpclib.Binary(open(metalink, 'rb').read()), options, position)
        else:
            return self.server.aria2.addMetalink(xmlrpclib.Binary(open(metalink, 'rb').read()), options, position)
    

    def remove(self, gid):
        '''
        This method removes the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of removed download.
        '''
        
        if self.useSecret:
            return self.server.aria2.remove("token:"+self.fixedSecret, gid)
        else:
            return self.server.aria2.remove(gid)
    

    def forceRemove(self, gid):
        '''
        This method removes the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of removed download.
        '''
        
        if self.useSecret:
            return self.server.aria2.forceRemove("token:"+self.fixedSecret, gid)
        else:
            return self.server.aria2.forceRemove(gid)
    

    def pause(self, gid):
        '''
        This method pauses the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of paused download.
        '''
        
        if self.useSecret:
            return self.server.aria2.pause("token:"+self.fixedSecret, gid)
        else:
            return self.server.aria2.pause(gid)
    

    def pauseAll(self):
        '''
        This method is equal to calling aria2.pause() for every active/waiting download.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.pauseAll("token:"+self.fixedSecret)
        else:
            return self.server.aria2.pauseAll()
    

    def forcePause(self, gid):
        '''
        This method pauses the download denoted by gid.

        gid: string, GID.

        return: This method returns GID of paused download.
        '''
        
        if self.useSecret:
            return self.server.aria2.forcePause("token:"+self.fixedSecret, gid)
        else:
            return self.server.aria2.forcePause(gid)
    

    def forcePauseAll(self):
        '''
        This method is equal to calling aria2.forcePause() for every active/waiting download.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.forcePauseAll("token:"+self.fixedSecret)
        else:
            return self.server.aria2.forcePauseAll()
    

    def unpause(self, gid):
        '''
        This method changes the status of the download denoted by gid from paused to waiting.

        gid: string, GID.

        return: This method returns GID of unpaused download.
        '''
        
        if self.useSecret:
            return self.server.aria2.unpause("token:"+self.fixedSecret, gid)
        else:
            return self.server.aria2.unpause(gid)
    

    def unpauseAll(self):
        '''
        This method is equal to calling aria2.unpause() for every active/waiting download.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.unpauseAll("token:"+self.fixedSecret)
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
            return self.server.aria2.tellStatus("token:"+self.fixedSecret, gid, keys)
        else:
            return self.server.aria2.tellStatus(gid, keys)
    

    def getUris(self, gid):
        '''
        This method returns URIs used in the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getUris("token:"+self.fixedSecret, gid)
        else:
            return self.server.aria2.getUris(gid)
    

    def getFiles(self, gid):
        '''
        This method returns file list of the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getFiles("token:"+self.fixedSecret, gid)
        else:
            return self.server.aria2.getFiles(gid)
    

    def getPeers(self, gid):
        '''
        This method returns peer list of the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getPeers("token:"+self.fixedSecret, gid)
        else:
            return self.server.aria2.getPeers(gid)
    

    def getServers(self, gid):
        '''
        This method returns currently connected HTTP(S)/FTP servers of the download denoted by gid.

        gid: string, GID.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getServers("token:"+self.fixedSecret, gid)
        else:
            return self.server.aria2.getServers(gid)
    

    def tellActive(self, keys=None):
        '''
        This method returns the list of active downloads.

        keys: keys for method response.

        return: The method response is of type list and its element is of type dict and it contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.tellActive("token:"+self.fixedSecret, keys)
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
            return self.server.aria2.tellWaiting("token:"+self.fixedSecret, offset, num, keys)
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
            return self.server.aria2.tellStopped("token:"+self.fixedSecret, offset, num, keys)
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
            return self.server.aria2.changePosition("token:"+self.fixedSecret, gid, pos, how)
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
            return self.server.aria2.changeUri("token:"+self.fixedSecret, gid, fileIndex, delUris, addUris, position)
        else:
            return self.server.aria2.changeUri(gid, fileIndex, delUris, addUris, position)
    

    def getOption(self, gid):
        '''
        This method returns options of the download denoted by gid.

        gid: string, GID.

        return: The response is of type dict.
        '''
        
        if self.useSecret:
            return self.server.aria2.getOption("token:"+self.fixedSecret, gid)
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
            return self.server.aria2.changeOption("token:"+self.fixedSecret, gid, options)
        else:
            return self.server.aria2.changeOption(gid, options)
    

    def getGlobalOption(self):
        '''
        This method returns global options.

        return: The method response is of type dict.
        '''
        
        if self.useSecret:
            return self.server.aria2.getGlobalOption("token:"+self.fixedSecret)
        else:
            return self.server.aria2.getGlobalOption()
    

    def changeGlobalOption(self, options):
        '''
        This method changes global options dynamically.

        options: dict, the options.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.changeGlobalOption("token:"+self.fixedSecret, options)
        else:
            return self.server.aria2.changeGlobalOption(options)
    

    def getGlobalStat(self):
        '''
        This method returns global statistics such as overall download and upload speed.

        return: The method response is of type struct and contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getGlobalStat("token:"+self.fixedSecret)
        else:
            return self.server.aria2.getGlobalStat()
    

    def purgeDownloadResult(self):
        '''
        This method purges completed/error/removed downloads to free memory.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.purgeDownloadResult("token:"+self.fixedSecret)
        else:
            return self.server.aria2.purgeDownloadResult()
    

    def removeDownloadResult(self, gid):
        '''
        This method removes completed/error/removed download denoted by gid from memory.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.removeDownloadResult("token:"+self.fixedSecret, gid)
        else:
            return self.server.aria2.removeDownloadResult(gid)
    

    def getVersion(self):
        '''
        This method returns version of the program and the list of enabled features.

        return: The method response is of type dict and contains following keys.
        '''
        
        if self.useSecret:
            return self.server.aria2.getVersion("token:"+self.fixedSecret)
        else:
            return self.server.aria2.getVersion()
    

    def getSessionInfo(self):
        '''
        This method returns session information.

        return: The response is of type dict.
        '''
        
        if self.useSecret:
            return self.server.aria2.getSessionInfo("token:"+self.fixedSecret)
        else:
            return self.server.aria2.getSessionInfo()
    

    def shutdown(self):
        '''
        This method shutdowns aria2.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.shutdown("token:"+self.fixedSecret)
        else:
            return self.server.aria2.shutdown()
    

    def forceShutdown(self):
        '''
        This method shutdowns aria2.

        return: This method returns OK for success.
        '''
        
        if self.useSecret:
            return self.server.aria2.forceShutdown("token:"+self.fixedSecret)
        else:
            return self.server.aria2.forceShutdown()
    
    def isAria2rpcRunning(self):
        #I need to check if _the aria2c I NEED_ exists, not some random aria2c instance!
        try:
            self.getVersion()
            return True
        except socket.error:
            return False

def isAria2Installed():
    for cmdpath in os.environ['PATH'].split(':'):
        if os.path.isdir(cmdpath) and 'aria2c' in os.listdir(cmdpath):
            return True

    return False


