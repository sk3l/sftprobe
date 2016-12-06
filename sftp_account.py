#!/opt/bb/bin/python3.5

import json
import logging
import random
import sys
import threading

from filegen import filegen

class sftp_account:

    logger =  logging.getLogger('sftp_test.account')
    def __init__(self, name,  user, pswd, path, cnt=1, size=1*pow(2,20), maxsize=0):
        self.name_          = name
        self.username_      = user
        self.password_      = pswd
        # Parameters influencing data file generation
        self.file_path_     = path
        self.file_cnt_      = cnt 
        self.file_size_     = size 
        self.file_size_max_ = maxsize
        self.file_list_     = []

        # Dictionary for tracking which files have been PUT to server
        # self.file_put_map_  = {}
        
        # Locks to synchronize processing the account's files.
        # Don't want worker threads simultanesouly put/get account's files
        self.file_locks_    = {}


    def create_data_files(self, contents="", cnt=0, size=0, maxsize=0):
        
        fcount = self.file_cnt_
        if cnt > 0:
            fcount = cnt

        fsize = self.file_size_
        if size > 0:
            fsize = size

        fmaxsize = self.file_size_max_
        if maxsize > 0:
            fmaxsize = maxsize
        
        filecnt = len(self.file_list_) + 1
        datalen = fsize 

        if fmaxsize > 0 and fmaxsize < fsize:
            sftp_account.logger.warn(
            "sftp_account::create_files invoked with trivial maxsize.")
            fmaxsize = 0

        fgen = filegen()
        for i in range(0,fcount):
            
            if fmaxsize > 0:
                random.seed()
                datalen = random.randrange(fsize, fmaxsize)

            fname = self.file_path_ + "/" + self.name_ + "_datafile_" + str(i+1)
            if len(contents) > 0:
                fname += ".txt"
                fgen.gen_text(fname, contents, datalen)
            else:
                fname += ".dat"
                fgen.gen_rand(fname, datalen)
            
            self.file_list_.append(fname)
            self.file_locks_[fname] = threading.Lock()

    def load_data_files(self):
        i = 0

    @classmethod
    def json_decode(classobj, jsondict):
       
        if "AccountName" in jsondict:
            fcnt = 1
            if "FileCount" in jsondict:
                fcnt = jsondict["FileCount"]
            fsize = 1*pow(2,20)
            if "FileSize" in jsondict:
                fsize = jsondict["FileSize"]
            fmax = 0
            if "FileMaxSize" in jsondict:
                fmax = jsondict["FileMaxSize"]
            
            return sftp_account(
                jsondict["AccountName"],
                jsondict["UserName"],
                jsondict["Password"],
                jsondict["FilePath"],
                fcnt,
                fsize,
                fmax)
       
        if "Accounts" in jsondict:
            return jsondict["Accounts"]  

        return None

if __name__ == "__main__":

    print("Testing class sftp_account:")

    acct = sftp_account(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

    acct.create_data_files("DE0F", 4, 64, 128)
    acct.create_data_files("", 4, 512, 1024)
