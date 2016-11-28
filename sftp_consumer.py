#!/opt/bb/bin/python3.5

import concurrent.futures
import threading

from sftp_account   import sftp_account

class sftp_consumer:
    
    def __init__(self, threadpool):
        self.thread_pool_ = threadpool

    def process_job(self, account, op, fname):
        print(
        "SFTP consumer thread#{3} processing {0} of file '{1}' from account '{2}'".format(
            op, fname, account.name_,threading.get_ident()))
