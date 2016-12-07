#!/opt/bb/bin/python3.5

import argparse
import concurrent.futures
import json
import logging
import multiprocessing
import re 
import sys
import time
import threading

from sftp_account   import sftp_account
from sftp_consumer  import sftp_consumer
from sftp_producer  import sftp_producer

def byte_size(fsizestr):
    fsMatch = re.search('(\d+)\s*([gkm]?b?)', fsizestr, re.I)

    if not fsMatch:
        return -1

    size = int(fsMatch.group(1))
    base = fsMatch.group(2).lower()

    if len(base) == 0:
        return size
    elif base.startswith("k"):
        return size * pow(2,10)
    elif base.startswith("m"):
        return size * pow(2,20)
    elif base.startswith("g"):
        return size * pow(2,30)
    else:
        return -1

log_mod = "sftp_test"

if __name__ == "__main__":

    logger = None
    try:

        ap = argparse.ArgumentParser(add_help=False)
 
        ap.add_argument(
            "-s", "--server", required=True,
            help="Address of server to test against e.g. localhost:22.")
 
        ap.add_argument(
            "-m", "--mode", required=True,
            help="Mode of operation: choices are 'random' or 'scripted'.")
    
        ap.add_argument(
            "-a", "--accounts", required=True,
            help="FQN of account input JSON file")
  
        ap.add_argument(
            "-c", "--count", type=int,
            help="Number of test account files to transfer.")
    
        ap.add_argument(
            "-i", "--size",
            help="Size of the transfer input file e.g. 100Kb, 4Mb.")
    
        ap.add_argument(
            "-l", "--maxsize",
            help="Max size for randomly generated transfer input file e.g. 100Kb, 4Mb.")
    
        ap.add_argument(
            "-n", "--numlimit", type=int,
            help="Run until <numlimit> transfers hav occurred.")
    
        ap.add_argument(
            "-t", "--timelimit", type=int,
            help="Run until <timelimit> seconds have elapsed.")
        
        ap.add_argument(
            "-f", "--file",
            help="FQN of input script file.")
 
        ap.add_argument(
            "-w", "--workercnt",
            help="Number of workers in the thread pool (defaults to machine CPU core count)")

        ap.add_argument(
            "-v", "--verbosity",
            help="Verbosity level for native Python Logging framework (default=DEBUG)")

        ap.add_argument("-h", "--help", action='store_true')
   
        if len(sys.argv) < 2:
            ap.print_help()
            exit(16)

        args = ap.parse_args()
    
        if vars(args)["help"]:
            ap.print_help()
            exit(16)

        logger = logging.getLogger(log_mod)

        verbosity = "DEBUG"
        if vars(args)["verbosity"]:
            verbosity = args.verbosity

        logger.setLevel(verbosity)

        formatter = logging.Formatter('%(asctime)s - %(name)s (%(levelname)s) - %(message)s')

        consHandler = logging.StreamHandler()
        consHandler.setLevel(verbosity)
        consHandler.setFormatter(formatter)
        logger.addHandler(consHandler)

        fileHandler = logging.FileHandler(
                        time.strftime("sftp_test_log_%H_%M_%m_%d_%Y.txt"))
        fileHandler.setLevel(verbosity)
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)

        cliSize = 0
        if vars(args)["size"]:
            cliSize = byte_size(args.size)
            if cliSize < 0:
                logger.critical("Bad --size argument.")
                ap.print_help()
                exit(16)

        cliMaxSize = 0
        if vars(args)["maxsize"]:
            cliMaxSize = byte_size(args.maxsize)
            if cliMaxSize < 0:
                logger.critical("Bad --maxsize argument.")
                ap.print_help()
                exit(16)


        #workQueue = queue.Queue()   # queue of SFTP tasks
        accountList = []            # list of SFTP test accounts
 
        # Deserialize the account file
        with open(args.accounts, "r") as acctf:
            accountList = json.load(acctf, object_hook=sftp_account.json_decode)
           
            for acct in accountList:

                logger.info("Found account '{0}' in input file.".format(acct.name_))

                cnt     = args.count if vars(args)["count"] else acct.file_cnt_
                size    = cliSize    if cliSize > 0         else acct.file_size_
                maxsize = cliMaxSize if cliMaxSize > 0      else acct.file_size_max_

                if size < 0:
                    logger.warn("Encountered bad file size paramter in account {0}; skipping.".format(
                        acct.name_))
                    continue
                elif maxsize <0:
                    logger.warn("Encountered bad file maxsize paramter in account {0}; skipping.".format(
                        acct.name_))
                    continue

                acct.create_data_files("", cnt, size, maxsize)
                
                logger.info("Created data files for account '{0}', count={1}, size={2}, maxsize={3}".format(
                    acct.name_, cnt, size, maxsize))
 
       
        # Use the supplied worker count, or <system_cpu_cnt>
        threadCnt = multiprocessing.cpu_count() 
        if vars(args)["workercnt"]:
            threadCnt = int(args.workercnt)

        with concurrent.futures.ThreadPoolExecutor(max_workers=threadCnt) as threadPool:
            producerTarget = None
            producerArgs   = ()
 
            consumer = sftp_consumer(threadPool, args.server)
            producer = sftp_producer(threadPool, consumer.process_job, accountList)       

            # Establish program mode & parameters
            mode = args.mode.lower()
            if mode == "random":
                transLimit = 0
                if vars(args)["numlimit"]:
                    transLimit = args.numlimit
                
                timelimit = 0
                if vars(args)["timelimit"]:
                    timelimit = args.timelimit

                producerTarget = producer.start_random
                producerArgs = (transLimit,timelimit,)
        
            elif mode == "scripted":
                if not vars(args)["file"]:
                    logger.critical("Must provide a script file for --file mode.")
                    ap.print_help()
                    exit(16)
                producerTarget = producer.start_scripted
                producerArgs = (args.file,)
        
            else:
                logger.critical("'{0}' is not a valid run mode.".format(mode))
                ap.print_help()
                exit(16)
 
            prodThread = threading.Thread(target=producerTarget,args=producerArgs)

            logger.info("Beginning SFTP test data production.")
            # Fire up the producer thread to create SFTP jobs
            prodThread.start()
            prodThread.join()

            # Wait until all of the SFTP jobs have been processed by the consumer
            while True:
                if producer.wait_for_consumer():
                    break

        logger.info("\nSFTP testing complete.")
        logger.info("\tResults:")
        logger.info("\t========")
        logger.info("\tNumber of SFTP operations sourced:    {0}".format(producer.trans_count_))
        logger.info("\tNumber of SFTP operations completed:  {0}".format(producer.complete_count_))
        if producer.error_count_ > 0:
            logger.info("\tNumber of SFTP operations failed:     {0}".format(producer.error_count_))
        if producer.cancel_count_ > 0:
            logger.info("\tNumber of SFTP operations canceled:   {0}".format(producer.cancel_count_))

    except Exception as e:
        msg = "Encountered exception: {0}".format(e)
        if logger:
            logger.critical(msg)
        else:
            print(msg)
        exit(32)
