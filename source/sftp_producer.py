#!/opt/bb/bin/python3.5

import json
import logging
import os
import random
import time
import threading

from sftp_account import sftp_account

class sftp_producer:

    logger =  logging.getLogger('sftp_test.producer')
    def __init__(self):
        self.trans_count_   = 0
        self.stop_          = threading.Event()
        # keep the accounts hashed by name
        #self.account_map_   = {}
        #for account in self.account_list_:
        #    self.account_map_[account.name_] = account

    # Main producer thread method for working through a pre-prepared set of
    # SFTP file operations from among the specified account list
    def start_scripted(self, scriptloc, enqueuefunc):

        # Perform SFTP tranfers, working off of the input script,
        # of until a count/time limit has been reached
        try:
            workScript = None
            with open(scriptloc, "r") as scriptf:
                workScript = json.load(scriptf)

            for job in workScript["Jobs"]:
                if self.stop_.isSet():
                    break
                
                #if not job["Account"] in self.account_map_:
                #    sftp_producer.logger.warn(
                #    "encountered unknown account {0} in work script.".format(
                #        job["Account"]))
                #    continue
                #account     = self.account_map_[job["Account"]]
    
                operation   = job["Operation"]
                cmd         = operation["Command"]
                params      = operation["Parameters"]
 
                # Post the job on the work queue
                enqueuefunc(account, cmd, params)

                self.trans_count_ += 1
        except Exception as e:
            msg = "Encountered an error in start_scripted thread: {0}".format(e)
            sftp_producer.logger.error(msg)
            return 64

    # Main producer thread method for creating a set of randomized SFTP file
    # operations from among the specified account list
    def start_random(self, acctlist, translimit, timelimit, enqueuefunc):
        try:
            random.seed()

            stoptime = 0
            if timelimit > 0:
                stoptime = time.time() + timelimit

            while True:

                if self.stop_.isSet():
                    break

                if translimit > 0 and self.trans_count_ >= translimit:
                    sftp_producer.logger.info(
                    "Terminating SFTP random production (trans limit reached)")
                    break

                if stoptime > 0 and time.time() >= stoptime:
                    sftp_producer.logger.info(
                    "Terminating SFTP random production (time limit reached)")
                    break
               
                # Select a random account, file and cmd 
                i = random.randrange(0, len(acctlist))
                account = acctlist[i]
                
                i = random.randrange(0, len(account.file_list_))
                fname = account.file_list_[i]
               
                with account.file_locks_[fname]:
                
                    (pathstr,filestr) = os.path.split(fname)
                
                    cmd = "PUT"
                    params = {"LocalPath": fname, "RemotePath": filestr, "SerialNo" : self.trans_count_} 
                    #if random.random() > .5: #and fname in account.file_put_map_:
                    #    cmd = "GET"
    
                    # Post the job on the work queue
                    enqueuefunc(account, cmd, params)
   
                self.trans_count_ += 1
        except Exception as e:
            msg = "Encountered error in start_random thread: {0}".format(e)
            sftp_producer.logger.error(msg)
            return 64


    def stop(self):
        self.stop_.set()
