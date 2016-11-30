#!/opt/bb/bin/python3.5

import concurrent.futures
import json
import random
import threading

from sftp_account import sftp_account

#class sftp_job:
#
#    def __init__(self, account, op, fname):
#        self.account_   = account
#        self.operation_ = op
#        self.file_name_ = fname

class sftp_producer:

    def __init__(self, threadpool, callback, acctlist):
        self.thread_pool_   = threadpool 
        self.thread_cback_  = callback
        self.account_list_  = acctlist
        self.trans_count_   = 0
        self.future_list_   = []
        self.stop_          = threading.Event()

    # Main producer thread method for working through a pre-prepared set of
    # SFTP file operations from among the specified account list
    def start_scripted(self, scriptloc):

        # Perform SFTP tranfers, either working off of the input script,
        # of until a count/time limit has been reached
        
        workScript = None
        with open(scriptloc, "r") as scriptf:
            workScript = json.load(scriptf)

        for job in workScript["Jobs"]:
            if self.stop_.isSet():
                break
            
            self.trans_count_ += 1

    # Main producer thread method for creating a set of randomized SFTP file
    # operations from among the specified account list
    def start_random(self, translimit):
        random.seed()
        while self.trans_count_ < translimit:
            
            if self.stop_.isSet():
                break
           
            # Select a random account, file and op
            account = self.account_list_[random.randrange(0, len(self.account_list_))]
            fname = account.file_list_[random.randrange(0, len(account.file_list_))]
            op = "PUT"
            if random.random() > .5 and fname in account.file_put_map_:
                op = "GET"

            # Post the job on the thread pool
            self.future_list_.append(
                self.thread_pool_.submit(self.thread_cback_, account, op, fname))

            self.trans_count_ += 1

    def stop(self):
        self.stop_.set()

    def wait_for_consumer(self):
        i = 1
        for job in self.future_list_:
            try:
                job.result()
                i += 1
            except Exception as e:
                print(
                "Encountered error waiting for job {0} in sftp_producer: {1}".format(
                i, e))
