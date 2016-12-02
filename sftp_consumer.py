#!/opt/bb/bin/python3.5

import concurrent.futures
import threading

from sftp_account   import sftp_account
from sftp_client    import sftp_client

class sftp_result:
    def __init__(self, account, cmd, params, complete=True):
        self.account_   = account
        self.command_   = cmd
        self.parameters_= params
        self.complete_  = complete

class sftp_consumer:
    
    def __init__(self, threadpool, serveraddr):
        self.threadpool_  = threadpool
        self.server_addr_ = serveraddr 

    def process_job(self, account, cmd, params):

        fname = params["LocalPath"]
        if not fname in account.file_locks_:
            raise Exception(
                "Couldn't locate file lock for {0} in account {1}".format(
                    fname, account.name_))

        haveLock = False
        lock = account.file_locks_[fname]
        try:
            gotLock = lock.acquire(blocking=False)

            if not gotLock:
                # account file is in use, resubmit work to thread pool
                #print("File {0} busy; try again later.".format(fname))
                return sftp_result(account, cmd, params, False)

            haveLock = True
            
            print(
            "SFTP consumer thread#{3} processing {0} of file '{1}' from account '{2}'".format(
                cmd, fname, account.name_,threading.get_ident()))

            clientconn = sftp_client(
                self.server_addr_, account.username_, account.password_)

            if cmd.upper() == "PUT":
                clientconn.do_put(fname, params["RemotePath"])
                #account.file_put_map_[fname] = True

            elif cmd.upper() == "GET":
                clientconn.do_get(params["RemotePath"], fname)
            
            elif cmd.upper() == "LS":
                clientconn.do_listdir(params["RemotePath"])
            
            else:
                print("WARNING : unrecognized cmd {0} for {1} in {2}.".format(
                    cmd, fname, account.name_))

            return sftp_result(account, cmd, params)
        except Exception as err:
            #pdb.set_trace()
            print("Encountered error during {0} of {1} in {2}: '{3}'".format(
                cmd, fname, account.name_, err))
            return sftp_result(account, cmd, params, False)

        finally:
            if lock and haveLock:
                lock.release()
                lock = None
