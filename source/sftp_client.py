#!/usr/bin/python

from contextlib import contextmanager

import enum
import logging
import sys

from paramiko import Transport
from paramiko import SFTPClient

class sftp_commands(enum.Enum):
    Unknown     = 0
    List        = 1
    ChangeDir   = 2
    Put         = 3
    Get         = 4

class sftp_client:

    logger =  logging.getLogger('sftprobe.client')
    def __init__(self, servaddr, username="", password="", key=None):
        
        self.transport_ = Transport(servaddr)
        self.key_       = key
        self.user_      = username
        self.pwd_       = password
        self.session_   = None

    @classmethod
    def get_command(classobj, cmdstr):
        cmdustr = cmdstr.upper() 
        if cmdustr == "PUT":
            return sftp_commands.Put
        elif cmdustr == "GET":
            return sftp_commands.Get
        elif cmdustr == "LS":
            return sftp_commands.List
        elif cmdustr == "CD":
            return sftp_commands.ChangeDir
        else:
            raise Exception("Unknown SFTP command {0}".format(cmdstr))


    def connect(self):
        if not self.session_ and not self.transport_.is_active():
            if self.key_:               # Try private key, if available
                self.transport_.connect(username=self.user_, pkey=self.key_)
            elif len(self.pwd_) > 0:    # Next, try password, if available
                self.transport_.connect(username=self.user_, password=self.pwd_)
            else:                       # Try just the user name
                self.transport_.connect(username=self.user_)

            self.session_ = SFTPClient.from_transport(self.transport_)

    def close(self):
        if self.session_:
            self.session_.close()
            self.session_ = None
        self.transport_.close()
        self.transport_ = None

    def get_status(self):
        if self.transport_.is_active():
            peer = self.transport_.getpeername()
            return "Connected to host [{0}], port {1}.".format(
                peer[0], peer[1])
        else:
            return "Not connected."

    def exec_sftp_cmd(self, cmd, **kwargs):
        self.connect()

        if cmd == sftp_commands.List:
            return self.session_.listdir(kwargs["RemotePath"])

        elif cmd == sftp_commands.ChangeDir:
            return self.session_.chdir(kwargs["RemotePath"])

        elif cmd == sftp_commands.Get:
            file_attrs = self.session_.get(kwargs["RemotePath"], kwargs["LocalPath"]) 

        elif cmd == sftp_commands.Put:
            file_attrs = self.session_.put(kwargs["LocalPath"], kwargs["RemotePath"]) 

    def do_changedir(self, path):
        return self.exec_sftp_cmd(
            sftp_commands.ChangeDir,
            RemotePath=path if len(path) > 0 else None)

    def do_listdir(self, path):
        return self.exec_sftp_cmd(
            sftp_commands.List,
            RemotePath=path if len(path) > 0 else "." )
   
    def do_get(self, rpth, lpth):
        return self.exec_sftp_cmd(sftp_commands.Get, RemotePath=rpth, LocalPath=lpth)
    
    def do_put(self, lpth, rpth):
        return self.exec_sftp_cmd(sftp_commands.Put, LocalPath=lpth, RemotePath=rpth)

@contextmanager
def get_sftp_connection(servaddr, username="", password="", key=None):
    client = sftp_client(servaddr, username, password, key) 
    client.connect()
    yield client
    client.close()

if __name__ == "__main__":
    if len(sys.argv) < 5 or len(sys.argv) > 6:
        print("\nusage: sftp_client <host:port> <user> <pwd> <action> [<actionarg>]\n")
        sys.exit(12)

    try:
        sc = sftp_client(sys.argv[1], sys.argv[2], sys.argv[3])

        if sys.argv[4].upper() == "LS":
            print("Directory contents for server path {0}:".format(sys.argv[5]))
            for entry in sc.do_listdir(sys.argv[5]):
                print("\t{0}".format(entry))
            sys.exit(0)
        elif sys.argv[4].upper() == "GET":
            print("Copying remote file at path '{0}' to local host:".format(sys.argv[5]))
            sc.do_get(sys.argv[5], sys.argv[5])
        elif sys.argv[4].upper() == "PUT":
            print("Copying local file at path '{0}' to remote host:".format(sys.argv[5]))
            sc.do_put(sys.argv[5], sys.argv[5])

    except Exception as e:
        print("Encountered error in __main__: {0}".format(e))
        sys.exit(10)
