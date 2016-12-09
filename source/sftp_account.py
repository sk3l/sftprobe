#!/opt/bb/bin/python3.5

import json
import logging
import random
import sys

from paramiko.rsakey    import RSAKey
from paramiko.dsskey    import DSSKey
from filegen            import filegen

class sftp_account:

    logger =  logging.getLogger('sftp_test.account')
    def __init__(self,
            name,               # Descriptive account name
            user="",            # System user name
            pswd="",            # System user password
            key=None,           # System user private key (paramiko obj)
            path="",            # Path to the account's files
            cnt=1,              # Number of files
            size=1*pow(2,20),   # Min file size
            maxsize=0):         # Max file size

        self.name_          = name
        self.username_      = user
        self.password_      = pswd
        self.key_           = key
        # Parameters influencing data file generation
        self.file_path_     = path
        self.file_cnt_      = cnt 
        self.file_size_     = size 
        self.file_size_max_ = maxsize
        self.file_list_     = []

        # Dictionary for tracking which files have been PUT to server
        # self.file_put_map_  = {}

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

            fname = self.file_path_ + "/" + self.username_ + "_datafile_" + str(i+1)
            if len(contents) > 0:
                fname += ".txt"
                fgen.gen_text(fname, contents, datalen)
            else:
                fname += ".dat"
                fgen.gen_rand(fname, datalen)
            
            self.file_list_.append(fname)

    def load_data_files(self):
        i = 0

    # Given a pkey type and file location, open the file and create a Paramiko
    # private key with the specified algo type
    @classmethod
    def load_pkey(clasobj, keytype, location):
        kt = keytype.upper()
        if kt == "RSA":
           return RSAKey.from_private_key_file(location)

        elif kt == "DSA":
            return DSSKey.from_private_key_file(location)

        else:
            raise Exception(
                "Unknown key type '{0}' in sftp_account::load_pkey".format(
                    keytype))

    # Given a dict, create an sftp_account obj from the dict keys.
    @classmethod
    def from_json_dict(classobj, jdict):
        uname = ""
        if "UserName" in jdict:
            uname = jdict["UserName"]
        passwd = ""
        if "Password" in jdict:
            passwd = jdict["Password"]
        path = ""
        if "FilePath" in jdict:
            path = jdict["FilePath"]
        fcnt = 1
        if "FileCount" in jdict:
            fcnt = jdict["FileCount"]
        fsize = 1*pow(2,20)
        if "FileSize" in jdict:
            fsize = jdict["FileSize"]
        fmax = 0
        if "FileMaxSize" in jdict:
            fmax = jdict["FileMaxSize"]
        key = None
        if "Key" in jdict:
            key = jdict["Key"]

        return sftp_account(
            jdict["AccountName"],
            uname,
            passwd,
            key,
            path,
            fcnt,
            fsize,
            fmax)

    # This is the 'object_hook' callback method used by json.load() for
    # deserialization of sftp_account from JSON file
    @classmethod
    def json_decode(classobj, jsondict):

        if "Location" in jsondict:
            return  sftp_account.load_pkey(
                        jsondict["Type"],
                        jsondict["Location"])
       
        if "AccountName" in jsondict:
            return sftp_account.from_json_dict(jsondict)

        if "Accounts" in jsondict:
            return jsondict["Accounts"]

        return None


if __name__ == "__main__":

    print("Testing class sftp_account:")

    acct = sftp_account(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

    acct.create_data_files("DE0F", 4, 64, 128)
    acct.create_data_files("", 4, 512, 1024)
