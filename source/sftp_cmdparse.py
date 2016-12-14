#!/opt/bb/bin/python3.5

import logging

from sftp_client import sftp_client

class sftp_cmdparse:

    logger =  logging.getLogger('sftprobe.cmdparse')
    def __init__(self, addr):
        self.address_ = addr
