#!/usr/bin/python

import sys

from paramiko import Transport
from paramiko import SFTPClient

class sftp_client:

    def __init__(self, servaddr, username, password):
        try:
            self.transport_ = Transport(servaddr)
            self.user_      = username
            self.pwd_       = password
        except Exception as e:
            print("***Error caught in sftp_client::__init__!***")

    def do_listdir(self, path):
        try:
            self.transport_.connect(username=self.user_, password=self.pwd_)
            sftp_sess = SFTPClient.from_transport(self.transport_)
            return sftp_sess.listdir(path)

        except Exception as e:
            print("Encountered error in sftp_client::do_ls: {0}".format(e))
        finally:
            if self.transport_.is_active():
                self.transport_.close()
    
    def do_put(self, localpath, remotepath):
        try:
            self.transport_.connect(username=self.user_, password=self.pwd_)
            sftp_sess = SFTPClient.from_transport(self.transport_)
            file_attrs = sftp_sess.put(localpath, remotepath) 

        except Exception as e:
            print("Encountered error in sftp_client::do_put: {0}".format(e))
        finally:
            if self.transport_.is_active():
                self.transport_.close()
 
    def do_get(self, remotepath, localpath):
        try:
            self.transport_.connect(username=self.user_, password=self.pwd_)
            sftp_sess = SFTPClient.from_transport(self.transport_)
            file_attrs = sftp_sess.get(remotepath, localpath) 

        except Exception as e:
            print("Encountered error in sftp_client::do_get: {0}".format(e))
        finally:
            if self.transport_.is_active():
                self.transport_.close()
 

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
