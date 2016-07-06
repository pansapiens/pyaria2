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

ARIA_ERROR_CODES = {
    0: "If all downloads were successful.",
    1: "If an unknown error occurred.",
    2: "If time out occurred.",
    3: "If a resource was not found.",
    4: "If aria2 saw the specified number of 'resource not found' error. See --max-file-not-found option.",
    5: "If a download aborted because download speed was too slow. See --lowest-speed-limit option.",
    6: "If network problem occurred.",
    7: "If there were unfinished downloads. This error is only reported if all finished downloads were successful and there were unfinished downloads in a queue when aria2 exited by pressing Ctrl-C by an user or sending TERM or INT signal.",
    8: "If remote server did not support resume when resume was required to complete download.",
    9: "If there was not enough disk space available.",
    10: "If piece length was different from one in .aria2 control file. See --allow-piece-length-change option.",
    11: "If aria2 was downloading same file at that moment.",
    12: "If aria2 was downloading same info hash torrent at that moment.",
    13: "If file already existed. See --allow-overwrite option.",
    14: "If renaming file failed. See --auto-file-renaming option.",
    15: "If aria2 could not open existing file.",
    16: "If aria2 could not create new file or truncate existing file.",
    17: "If file I/O error occurred.",
    18: "If aria2 could not create directory.",
    19: "If name resolution failed.",
    20: "If aria2 could not parse Metalink document.",
    21: "If FTP command failed.",
    22: "If HTTP response header was bad or unexpected.",
    23: "If too many redirects occurred.",
    24: "If HTTP authorization failed.",
    25: "If aria2 could not parse bencoded file (usually '.torrent' file).",
    26: "If '.torrent' file was corrupted or missing information that aria2 needed.",
    27: "If Magnet URI was bad.",
    28: "If bad/unrecognized option was given or unexpected option argument was given.",
    29: "If the remote server was unable to handle the request due to a temporary overloading or maintenance.",
    30: "If aria2 could not parse JSON-RPC request.",
    31: "Reserved. Not used.",
    32: "If checksum validation failed.",
}

SAVE_SESSION_INTERVAL_DEFAULT = 60


SETTING_IGNORE_FIELDS = [
    "host",
]

class AriaServerSettings(object):
    def __init__(self, **kwargs):
        self.host = DEFAULT_HOST

        # Value Fields
        # Server Behavior
        self.rpc_listen_port = DEFAULT_PORT
        self.save_session = None
        self.input_file = None  # Should match save_session field
        self.save_session_interval = SAVE_SESSION_INTERVAL_DEFAULT
        self.rpc_max_request_size = None
        self.dir = None

        self.log = None
        self.check_integrity = None
        self.server_stat_of = None
        self.server_stat_if = None
        self.server_stat_timeout = None
        self.timeout = None

        # Proxy Settings
        self.all_proxy = None
        self.http_proxy = None
        self.https_proxy = None
        self.ftp_proxy = None
        self.http_proxy_user = None
        self.http_proxy_passwd = None
        self.all_proxy_user = None
        self.all_proxy_passwd = None
        self.proxy_method = None

        # Download Behavior
        self.max_concurrent_downloads = None
        self.max_connection_per_server = None
        self.max_download_limit = None
        self.connect_timeout = None
        self.dry_run = None
        self.lowest_speed_limit = None
        self.max_file_not_found = None
        self.max_tries = None
        self.min_split_size = None
        self.netrc_path = None
        self.no_netrc = None
        self.no_proxy = None
        self.remote_time = None
        self.retry_wait = None
        self.split = None
        self.stream_piece_selector = None
        self.uri_selector = None

        # HTTP Specific Options
        self.ca_certificate = None
        self.certificate = None
        self.check_certificate = None
        self.http_accept_gzip= None
        self.http_auth_challenge = None
        self.http_no_cache = None
        self.http_user = None
        self.http_passwd = None
        self.http_proxy = None
        self.http_proxy_passwd = None
        self.http_proxy_user = None
        self.https_proxy = None
        self.https_proxy_passwd = None
        self.https_proxy_user = None
        self.private_key = None
        self.referer = None
        self.enable_http_keep_alive = None
        self.enable_http_pipelining = None
        self.header = None
        self.load_cookies = None
        self.save_cookies = None
        self.use_head = None
        self.user_agent = None

        # FTP Specific Options
        self.ftp_user = None
        self.ftp_passwd = None
        self.ftp_pasv = None
        self.ftp_proxy = None
        self.ftp_proxy_passwd = None
        self.ftp_proxy_user = None
        self.ftp_type = None
        self.ftp_reuse_connection = None

        # Bittorrent Specific Options
        self.bt_detach_seed_only = None
        self.bt_enable_hook_after_hash_check = None
        self.bt_enable_lpd = None
        self.bt_exclude_tracker = None
        self.bt_external_ip = None
        self.bt_force_encryption = None
        self.bt_hash_check_seed = None
        self.bt_lpd_interface = None
        self.bt_max_open_files = None
        self.bt_max_peers = None
        self.bt_metadata_only = None
        self.bt_min_crypto_level = None
        self.bt_prioritize_piece = None
        self.bt_remove_unselected_file = None
        self.bt_require_crypto = None
        self.bt_request_peer_speed_limit = None
        self.bt_save_metadata = None
        self.bt_seed_unverified = None
        self.bt_stop_timeout = None
        self.bt_tracker = None
        self.bt_tracker_connect_timeout = None
        self.bt_tracker_interval = None
        self.bt_tracker_timeout = None
        self.dht_entry_point = None
        self.dht_entry_point6 = None
        self.dht_file_path = None
        self.dht_file_path6 = None
        self.dht_listen_addr6 = None
        self.dht_listen_port = None
        self.dht_message_timeout = None
        self.enable_dht = None
        self.enable_dht6 = None
        self.enable_peer_exchange = None
        self.follow_torrent = None
        self.index_out = None
        self.listen_port = None
        self.max_overall_upload_limit = None
        self.peer_id_prefix = None
        self.seed_ratio = None
        self.seed_time = None

        # Metalink Specific Options
        self.follow_metalink = None
        self.metalink_base_uri = None
        self.metalink_file = None
        self.metalink_language = None
        self.metalink_location = None
        self.metalink_os = None
        self.metalink_version = None
        self.metalink_preferred_protocol = None
        self.metalink_enable_unique_protocol = None

        # Flag Fields
        self.continue_flag = None

        # Other Fields
        self.rpc_secret = None

        self.__dict__.update(**kwargs)

    def check_parameters(self):
        pass

    def construct_as_command_line(self):
        to_set = {}
        for name, value in self.__dict__.items():
            if value is None:
                continue

            if name in SETTING_IGNORE_FIELDS:
                continue

            if name.startswith("_"):
                continue

            if name.endswith('_flag'):
                if not isinstance(value, bool):
                    raise ValueError("Param [%s] is a flag - set True/False" % name)
                name = name.replace("_flag", "")
            if isinstance(value, bool):
                value = str(value).lower()
            name = name.replace('_', '-')
            to_set[name] = value
        command = ' '.join(['--%s=%s' % (param, value) for param, value in to_set.items()])
        return command



class PyAria2(object):
    def __init__(self, server_settings=None):
        '''
        PyAria2 constructor.

        host: string, aria2 rpc host, default is 'localhost'
        port: integer, aria2 rpc port, default is 6800
        session: string, aria2 rpc session saving.
        :type server_settings: AriaServerSettings
        '''
        if server_settings is None:
            """
            Use default settings
            """
            server_settings = AriaServerSettings()

        if not LOWER_PORT_LIMIT <= server_settings.rpc_listen_port <= UPPER_PORT_LIMIT:
            raise Exception(
                "port is not between {0} and {1}".format(LOWER_PORT_LIMIT, UPPER_PORT_LIMIT)
            )

        self.useSecret = False
        if server_settings.rpc_secret is not None:
            self.useSecret = True
            self.rpcSecret = server_settings.rpc_secret

        if not isAria2Installed():
            raise Exception('aria2 is not installed, please install it before.')

        server_uri = SERVER_URI_FORMAT.format(server_settings.host, server_settings.rpc_listen_port)
        self.server = xmlrpclib.ServerProxy(server_uri, allow_none=True)

        if not isAria2rpcRunning():
            self.start_aria_server(server_settings)
        else:
            print('aria2 RPC server instance detected')

    def start_aria_server(self, server_settings):
        '''
        :type server_settings: AriaServerSettings
        '''
        command_line_params = server_settings.construct_as_command_line()
        cmd = 'aria2c {}'.format(command_line_params)

        if server_settings.save_session is not None:
            self.check_create_file(server_settings.input_file)

        aria_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        count = 0

        while True:
            time.sleep(0.5)
            if aria_process.poll() is not None:
                out, err = aria_process.communicate()
                if err:
                    print(out)
                    print(err)
                    raise Exception("Error starting aria server")
            if isAria2rpcRunning():
                break
            else:
                count += 1
                time.sleep(3)
            if count == 10:
                raise Exception('aria2 RPC server started failure.')

        print('aria2 RPC server is started.')

    def check_create_file(self, input_file_path):
        if os.path.exists(input_file_path):
            return

        open(input_file_path, 'a').close()

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
            binary_content = xmlrpclib.Binary(content)
            if self.useSecret:
                fixedsecretphrase = "token:{}".format(self.rpcSecret)
                return self.server.aria2.addTorrent(fixedsecretphrase, binary_content, uris, options, position)
            else:
                return self.server.aria2.addTorrent(binary_content, uris, options, position)

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
        print("Calling shutdown of aria2 server.")
        if self.useSecret:
            return self.server.aria2.shutdown("token:" + self.rpcSecret)
        else:
            return self.server.aria2.shutdown()

    def forceShutdown(self):
        '''
        This method shutdowns aria2.

        return: This method returns OK for success.
        '''
        print("Forcing shutdown of aria2 server.")
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
    resp_line = pgrep_process.stdout.readline()
    if resp_line == b'':
        return False
    else:
        return True
