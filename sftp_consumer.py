#!/opt/bb/bin/python3.5

import concurrent.futures
import os
import threading

from sftp_account   import sftp_account
from sftp_client    import sftp_client

class sftp_consumer:
    
    def __init__(self, serveraddr):
        self.server_addr_ = serveraddr 

    def process_job(self, account, op, fname):
        print(
        "SFTP consumer thread#{3} processing {0} of file '{1}' from account '{2}'".format(
            op, fname, account.name_,threading.get_ident()))

        if not fname in account.file_locks_:
            raise Exception(
                "Couldn't locate file lock for {0} in account {1}".format(
                    fname, account.name_))

        lock = account.file_locks_[fname]
        try:
            lock.acquire()

            clientconn = sftp_client(
                self.server_addr_, account.username_, account.password_)

            (pathstr,filestr) = os.path.split(fname)

            if op.upper() == "PUT":
                clientconn.do_put(fname, filestr)
            elif op.upper() == "GET":
                clientconn.do_get(filestr, fname)
            elif op.upper() == "LS":
                clientconn.do_listdir(fname)
            else:
                print("WARNING : unrecognized op {0} for {1} in {2}.".format(
                    op, fname, account.name_))

        except Exception as err:
            print("Encountered error during {0} of {1} in {2}: '{3}'".format(
                op, fname, account.name_, err))

        finally:
            if lock:
                lock.release()
                lock = None
