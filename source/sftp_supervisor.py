#!/opt/bb/bin/python3.5

import concurrent.futures
import logging
import threading

from sftp_consumer import sftp_status

class sftp_supervisor:
    logger =  logging.getLogger('sftp_test.supervisor')
    
    def __init__(self, threadcnt, prodfunc, prodargs, consfunc):
        self.complete_count_= 0 
        self.cancel_count_  = 0
        self.error_count_   = 0
 
        self.future_list_   = []
        self.thread_pool_   = concurrent.futures.ThreadPoolExecutor(
                                max_workers=threadcnt)

        self.producer_func_ = prodfunc
        self.producer_args_ = prodargs
        self.consumer_func_ = consfunc 

    def __enter__(self):
        return self

    def __exit__(self, exceptype, exceptval, traceback):
        self.thread_pool_.shutdown()

    def add_a_job(self, account, cmd, params):
        self.future_list_.append(
           self.thread_pool_.submit(self.consumer_func_, account, cmd, params))


    def process_jobs(self):

        self.producer_args_.append(self.add_a_job)
        pthread = threading.Thread(
                    target=self.producer_func_,args=self.producer_args_)

        # Fire up the producer thread to create SFTP jobs
        sftp_supervisor.logger.info("Beginning SFTP test data production.")
        pthread.start()
        pthread.join()

        # Wait until all of the SFTP jobs have been processed by the consumer
        sftp_supervisor.logger.info("Waiting for jobs to complete.")

        while True:
            if self.wait_for_jobs():
                break

    def wait_for_jobs(self):
        sftp_supervisor.logger.debug(
        "Results length in sftp_supervisor::wait_for_jobs: {0}".format(
            len(self.future_list_)))

        retry_list = []
        i = 1
        for job in self.future_list_:
            try:
                #if job.cancelled():
                #    continue

                res = job.result()
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

            except Exception as e:
                sftp_supervisor.logger.error(
                "Encountered error waiting for job {0} in sftp_supervisor: {1}".format(
                i, e))
            finally:
                i += 1

        self.future_list_.clear()
        
        # Resubmit any retries
        if len(retry_list) > 0:
            sftp_supervisor.logger.info(
            "Retrying {0} jobs for execution.".format(len(retry_list)))
            
            for res in retry_list:
                self.future_list_.append(
                    self.thread_pool_.submit(
                        self.consumer_func_, res.account_, res.command_,res.parameters_))

        if len(self.future_list_) > 0:
            return False
        else:
            return True

