#!/opt/bb/bin/python3.5

import concurrent.futures
import json
import os
import random
import time
import threading

from sftp_account import sftp_account
from sftp_consumer import sftp_result

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
        self.complete_count_= 0 
        self.cancel_count_  = 0
        self.future_list_   = []
        self.stop_          = threading.Event()

        # keep the accounts hashed by name
        self.account_map_   = {}
        for account in self.account_list_:
            self.account_map_[account.name_] = account

    # Main producer thread method for working through a pre-prepared set of
    # SFTP file operations from among the specified account list
    def start_scripted(self, scriptloc):

        # Perform SFTP tranfers, working off of the input script,
        # of until a count/time limit has been reached
        try:
            workScript = None
            with open(scriptloc, "r") as scriptf:
                workScript = json.load(scriptf)
    
            for job in workScript["Jobs"]:
                if self.stop_.isSet():
                    break
                
                if not job["Account"] in self.account_map_:
                    print(
                    "WARNING: encountered unknown account {0} in work script.".format(
                        job["Account"]))
                    continue
                account     = self.account_map_[job["Account"]]
    
                operation   = job["Operation"]
                cmd         = operation["Command"]
                params      = operation["Parameters"]
 
                # Post the job on the thread pool
                self.future_list_.append(
                    self.thread_pool_.submit(self.thread_cback_, account, cmd, params))
                

                self.trans_count_ += 1
        except Exception as e:
            print(
            "Encountered an error in start_scripted thread: {0}".format(
            e))
            return 64

    # Main producer thread method for creating a set of randomized SFTP file
    # operations from among the specified account list
    def start_random(self, translimit, timelimit):
        try:
            random.seed()

            stoptime = 0
            if timelimit > 0:
                stoptime = time.time() + timelimit

            while True:

                if self.stop_.isSet():
                    break

                if translimit > 0 and self.trans_count_ >= translimit:
                    print("Terminating SFTP random production (trans limit reached)")
                    break

                if stoptime > 0 and time.time() >= stoptime:
                    print("Terminating SFTP random production (time limit reached)")
                    self.cancel()
                    break
               
                # Select a random account, file and cmd 
                i = random.randrange(0, len(self.account_list_))
                account = self.account_list_[i]
                
                i = random.randrange(0, len(account.file_list_))
                fname = account.file_list_[i]
               
                with account.file_locks_[fname]:
                
                    (pathstr,filestr) = os.path.split(fname)
                
                    cmd = "PUT"
                    params = {"LocalPath": fname, "RemotePath": filestr, "SerialNo" : self.trans_count_} 
                    #if random.random() > .5: #and fname in account.file_put_map_:
                    #    cmd = "GET"
    
                    # Post the job on the thread pool
                    self.future_list_.append(
                        self.thread_pool_.submit(
                            self.thread_cback_, account, cmd, params))
    
                self.trans_count_ += 1
        except Exception as e:
            print(
            "Encountered error in start_random thread: {0}".format(
                e))
            return 64


    def stop(self):
        self.stop_.set()

    def cancel(self):
        print("DEBUG => len(future_list) in sftp_producer::cancel() = {0}".format(len(self.future_list_)))
        for job in self.future_list_:
            if not job.running() and not job.done():
                job.cancel()
                self.cancel_count_ += 1

    def wait_for_consumer(self):
       
        retry_list = []
        i = 1
        for job in self.future_list_:
            try:
                if job.cancelled():
                    continue

                res = job.result()
                if not res.complete_:
                    retry_list.append(res)
                else:
                    self.complete_count_ += 1
            except Exception as e:
                print(
                "Encountered error waiting for job {0} in sftp_producer: {1}".format(
                i, e))
            finally:
                i += 1

        self.future_list_.clear()
        # Resubmit the retries
        for res in retry_list:
            self.future_list_.append(
                self.thread_pool_.submit(
                    self.thread_cback_, res.account_, res.command_,res.parameters_))

        if len(self.future_list_) > 0:
            return False
        else:
            return True
