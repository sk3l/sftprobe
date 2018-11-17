#!/usr/bin/env python3

import concurrent.futures
import enum
import logging
import os

from timeit         import default_timer as stopwatch

from sftp_account   import sftp_account
from sftp_client    import sftp_client
from sftp_client    import get_sftp_connection

class sftp_status(enum.Enum):
    Unknown = -1
    Success = 0
    Blocked = 1
    Error   = 2

class sftp_result:
    def __init__(self, account, cmd, params, cmdtime=None, sesstime=None, status=sftp_status.Unknown):
        self.account_   = account
        self.command_   = cmd
        self.parameters_= params
        self.cmd_time_  = cmdtime  # elapsed 'wall clock' time for SFTP command
        self.sess_time_ = sesstime # elapsed 'wall clock' time for SFTP session
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

            # Collect elapsed time of SFTP ~~session~~ (START timer)
            start_sess_tm = stopwatch()
            with get_sftp_connection(
                    self.server_addr_,
                    account.username_,
                    account.password_,
                    account.key_)      as sftpconn:

                # Collect elapsed time of SFTP ~~command~~ (START timer)
                start_cmd_tm = stopwatch()
                sftpconn.exec_sftp_cmd(sftp_client.get_command(cmd), **params)
                # Collect elapsed time of SFTP ~~command~~ (STOP timer)
                stop_cmd_tm = stopwatch()

            # Collect elapsed time of SFTP ~~session~~ (STOP timer)
            stop_sess_tm = stopwatch()
            return sftp_result(
                    account,
                    cmd,
                    params,
                    stop_cmd_tm-start_cmd_tm,
                    stop_sess_tm-start_sess_tm,
                    sftp_status.Success)

        except Exception as err:
            errstr = "Encountered error during {0} ".format(cmd)
            if "LocalPath" in params:
                errstr += "of {0} ".format(params["LocalPath"])
            errstr += "in account {0}: '{1}'".format(account.name_, err)

            sftp_consumer.logger.error(errstr)
            return sftp_result(
                    account, cmd, params, None, None, sftp_status.Error)

