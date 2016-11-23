#!/usr/bin/python

import sys
import random

from filegen import filegen

class sftp_account:

    def __init__(self, name,  user, pswd, path):
        self.name_      = name
        self.username_  = user
        self.password_  = pswd
        self.path_      = path
        self.serialno_  = 0
        self.file_list_ = []

    def create_data_files(self, cnt=1, contents="", size=1*pow(2,20), maxsize=0):
        filecnt = len(self.file_list_) + 1
        datalen = size 

        if maxsize > 0 and maxsize < size:
            print("\sftp_account::create_files invoked with trivial \
maxsize; ignoring.".format(size))
            maxsize = 0

        fgen = filegen()
        for i in range(0,cnt):
            
            if maxsize > 0:
                random.seed()
                datalen = random.randrange(size, maxsize)

            fname = self.name_ + "_datafile_" + str(i)
            if len(contents) < 1:
                fname += ".txt"
                fgen.gen_text(fname, contents, datalen)
            else:
                fname += ".dat"
                fgen.gen_rand(fname, datalen)
            
            self.file_list_.append(fname)
            print("Generated data file '{0}' for sftp account {1}.".format(fname, self.name_))


if __name__ == "__main__":

    print("Testing class sftp_account:")

    acct = sftp_account(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

    acct.create_data_files(4, "DE0F", 256, 512)
    acct.create_data_files(4, "", 1024, 4096)
