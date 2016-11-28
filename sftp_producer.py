#!/usr/bin/python

import json
import time

class sftp_producer:

    def __init__(translimit=0, scriptloc=""):
        self.trans_count_   = 0
        self.trans_limit_   = translimit
        self.script_loc_    = scriptloc

    def start():

        workScript = None   # Use if the work set is scripted
        
        if scriptloc != "":
            with open(scriptloc, "r") as scriptf:
                workScript = json.load(scriptf)

        while True:
            # Perform SFTP tranfers, either working off of the input script,
            # of until a count/time limit has been reached

            self.trans_count_ += 1
        


