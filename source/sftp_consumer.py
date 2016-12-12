#!/opt/bb/bin/python3.5

import concurrent.futures
import enum
import logging
import threading

from sftp_account   import sftp_account
from sftp_client    import sftp_client

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
    
    logger =  logging.getLogger('sftp_test.consumer')
    def __init__(self, serveraddr):
        self.server_addr_ = serveraddr 

    def process_job(self, account, cmd, params):

        try:
            fname = ""
            if "LocalPath" in params:
                fname = params["LocalPath"]
            
            serialno = 0
            if "SerialNo" in params:
                serialno = params["SerialNo"] 
         
            dbgstr = "SFTP consumer {0} processing {1} ".format(
                threading.current_thread().name, cmd)
                                      
            if len(fname) > 0:
                dbgstr += "of file '{0}' ".format(fname)

            dbgstr += "from account '{0}'".format(account.name_)

            if "SerialNo" in params:
                dbgstr += " (serial# {0})".format(serialno)

            sftp_consumer.logger.debug(dbgstr)

            clientconn = sftp_client(
                self.server_addr_, account.username_, account.password_, account.key_)

            if cmd.upper() == "PUT":
                rpath = params["RemotePath"]
                if serialno > 0:
                    rpath += "_" + str(serialno)

                clientconn.do_put(fname, rpath)

            elif cmd.upper() == "GET":
                clientconn.do_get(params["RemotePath"], fname)
            
            elif cmd.upper() == "LS":
                clientconn.do_listdir(params["RemotePath"])
            
            else:
                lgger.warn("unrecognized cmd {0} for {1} in {2}.".format(
                    cmd, fname, account.name_))

            return sftp_result(account, cmd, params, sftp_status.Success)
        except Exception as err:
            sftp_consumer.logger.error("Encountered error during {0} of {1} in {2}: '{3}'".format(
                cmd, fname, account.name_, err))
            return sftp_result(account, cmd, params, sftp_status.Error)

