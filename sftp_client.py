#!/usr/bin/python

import enum
import logging
import sys

from paramiko import Transport
from paramiko import SFTPClient

class sftp_commands(enum.Enum):
    Unknown = 0
    List    = 1
    Put     = 2
    Get     = 3

class sftp_client:

    def __init__(self, servaddr, username, password):
        #import paramiko
        #logger = paramiko.util.logging.getLogger()
        #logger.propagate = False 
        
        self.transport_ = Transport(servaddr)
        self.user_      = username
        self.pwd_       = password

    def exec_sftp_cmd(self, cmd, **kwargs):
        try:
            self.transport_.connect(username=self.user_, password=self.pwd_)
            sftp_sess = SFTPClient.from_transport(self.transport_)
            
            if cmd == sftp_commands.List:
                return sftp_sess.listdir(kwargs["remotepath"])
            
            elif cmd == sftp_commands.Get:
                file_attrs = sftp_sess.get(kwargs["remotepath"], kwargs["localpath"]) 
            
            elif cmd == sftp_commands.Put:
                file_attrs = sftp_sess.put(kwargs["localpath"], kwargs["remotepath"]) 

        except Exception as e:
            print("Encountered error in sftp_client::{1}: {0}".format(e, cmd))
        finally:
            if self.transport_.is_active():
                self.transport_.close()

    def do_listdir(self, path):
        return self.exec_sftp_cmd(sftp_commands.List, remotepath=path)
   
    def do_get(self, rpth, lpth):
        return self.exec_sftp_cmd(sftp_commands.Get, remotepath=rpth, localpath=lpth)
    
    def do_put(self, lpth, rpth):
        return self.exec_sftp_cmd(sftp_commands.Put, localpath=lpth, remotepath=rpth)

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
