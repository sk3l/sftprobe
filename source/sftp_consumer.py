#!/opt/bb/bin/python3.5

import concurrent.futures
import enum
import logging
import os

from sftp_account   import sftp_account
from sftp_client    import sftp_client
from sftp_client    import get_sftp_connection

class sftp_status(enum.Enum):
    Unknown = -1
    Success = 0
    Blocked = 1
    Error   = 2

class sftp_result:
    def __init__(self, account, cmd, params, status=sftp_status.Unknown):
        self.account_   = account
        self.command_   = cmd
        self.parameters_= params
        self.status_    = status

class sftp_consumer:
    
    logger =  logging.getLogger('sftprobe.consumer')
    def __init__(self, serveraddr):
        self.server_addr_ = serveraddr 

    def process_command(self, account, cmd, params):

        try:
            dbgstr = "SFTP consumer {0} processing {1} ".format(
                os.getpid(), cmd)
            if "LocalPath" in params:
                dbgstr += "of file '{0}' ".format(params["LocalPath"])

            dbgstr += "from account '{0}'".format(account.name_)

            # If there's a serial number and remote path present,
            # append the serial number to the remote path to make
            # unique file names on remote host
            if "SerialNo" in params:
                dbgstr += " (serial# {0})".format(params["SerialNo"])
                if "RemotePath" in params:
                    params["RemotePath"] = "{0}_{1}".format(
                                            params["RemotePath"], 
                                            params["SerialNo"])

            sftp_consumer.logger.debug(dbgstr)

            with get_sftp_connection(
                    self.server_addr_, 
                    account.username_, 
                    account.password_, 
                    account.key_)      as sftpconn:

                sftpconn.exec_sftp_cmd(sftp_client.get_command(cmd), **params)

            return sftp_result(account, cmd, params, sftp_status.Success)
        except Exception as err:
            errstr = "Encountered error during {0} ".format(cmd)
            if "LocalPath" in params:
                errstr += "of {0} ".format(params["LocalPath"])
            errstr += "in account {0}: '{1}'".format(account.name_, err)

            sftp_consumer.logger.error(errstr)
            return sftp_result(account, cmd, params, sftp_status.Error)

