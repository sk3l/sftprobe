#!/usr/bin/env python3

import concurrent.futures
import logging
import numpy

from sftp_consumer import sftp_status

class sftp_supervisor:
    logger =  logging.getLogger('sftprobe.supervisor')

    def __init__(self, workercnt, prodfunc, prodargs, consfunc):
        self.complete_count_= 0
        self.cancel_count_  = 0
        self.error_count_   = 0
        self.cmd_avg_time_  = 0.0
        self.sess_avg_time_ = 0.0
        self.future_list_   = []
        self.process_pool_   = concurrent.futures.ProcessPoolExecutor(
                                max_workers=workercnt)

        self.producer_func_ = prodfunc
        self.producer_args_ = prodargs
        self.consumer_func_ = consfunc

    def __enter__(self):
        return self

    def __exit__(self, exceptype, exceptval, traceback):
        self.process_pool_.shutdown()

    def add_a_command(self, account, cmd, params):
        self.future_list_.append(
           self.process_pool_.submit(self.consumer_func_, account, cmd, params))


    def execute_commands(self):

        returnvals = {}

        self.producer_args_.append(self.add_a_command)
        self.producer_args_.append(returnvals)

        # Fire up the producer to create SFTP commands
        sftp_supervisor.logger.info("Beginning SFTP test data production.")
        self.producer_func_(*self.producer_args_)

        if "timeout" in returnvals and returnvals["timeout"]:
            sftp_supervisor.logger.info("Cancelling queued commands.")
            self.cancel()

        # Wait until all of the SFTP coammands have been processed by the consumer
        sftp_supervisor.logger.info("Waiting for commands to complete.")

        self.wait_for_commands()

    def cancel(self):
        for command in self.future_list_:
            if not command.running() and not command.done():
                command.cancel()
                self.cancel_count_ += 1

    def wait_for_commands(self):
        sftp_supervisor.logger.debug(
        "Results length in sftp_supervisor::wait_for_commands: {0}".format(
            len(self.future_list_)))

        cmd_time_list = []
        sess_time_list = []

        i = 1
        for command in self.future_list_:
            try:
                if command.cancelled():
                    continue

                res = command.result()
                if res.status_ == sftp_status.Blocked:
                    retry_list.append(res)
                elif res.status_ == sftp_status.Error:
                    self.error_count_ += 1
                elif res.status_ == sftp_status.Success:
                    self.complete_count_ += 1
                else:
                    sftp_supervisor.logger.warn(
                    "Unknown SFTP result for account={0}, cmd={1}, params={2}".format(
                        res.account_, res.command_, res.parameters_))

                if res.cmd_time_ is not None:
                    cmd_time_list.append(res.cmd_time_)

                if res.sess_time_ is not None:
                    sess_time_list.append(res.sess_time_)

            except Exception as e:
                sftp_supervisor.logger.error(
                "Encountered error waiting for command {0} in sftp_supervisor: {1}".format(
                i, e))
            finally:
                i += 1
        #import pdb;pdb.set_trace()
        self.cmd_avg_time_ = numpy.mean(cmd_time_list)
        self.sess_avg_time_= numpy.mean(sess_time_list)
