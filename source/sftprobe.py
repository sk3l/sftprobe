#!/opt/bb/bin/python3.5

import json
import logging
import multiprocessing
import re 
import sys
import time

from sftp_argparse      import sftp_argparse
from sftp_account       import sftp_account
from sftp_consumer      import sftp_consumer
from sftp_producer      import sftp_producer
from sftp_supervisor    import sftp_supervisor 

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
        ap = sftp_argparse()

        args = ap.parse_args()
    
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

        # Establish program command & parameters
        command = args.command

        # Create the sftp job producer 
        producer = sftp_producer() 
               
        prodFunc = None # producer func to create jobs
        prodArgs   = [] # producer args for job creation 
 
        # Create the sftp job consumer 
        consumer = sftp_consumer(args.address)
        consFunc = consumer.process_job


        # Determine which job production method to use based on program args

        # #####################################################################
        # Randomly generate the SFTP jobs
        if command == "flood":
            transLimit = 0
            if vars(args)["numlimit"]:
                transLimit = args.numlimit
            
            timelimit = 0
            if vars(args)["timelimit"]:
                timelimit = args.timelimit

            transRate = 0
            if vars(args)["rate"]:
                transRate = args.rate

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

            accountList = []
     
            # Deserialize the account file
            with open(args.accounts, "r") as acctf:
                accountList = json.load(acctf, object_hook=sftp_account.json_decode)
               
                for acct in accountList:
    
                    logger.info("Found account '{0}' in input file.".format(acct.name_))
    
                    cnt     = args.count if vars(args)["count"] else acct.file_cnt_
                    size    = cliSize    if cliSize > 0         else acct.file_size_
                    maxsize = cliMaxSize if cliMaxSize > 0      else acct.file_size_max_
    
                    if size < 0:
                        logger.warn(
                        "Encountered bad file size paramter in account {0}; skipping.".format(
                            acct.name_))
                        continue
                    elif maxsize <0:
                        logger.warn(
                        "Encountered bad file maxsize paramter in account {0}; skipping.".format(
                            acct.name_))
                        continue
    
                    acct.create_data_files("", cnt, size, maxsize)
                    
                    logger.info(
                    "Created data files for account '{0}', count={1}, size={2}, maxsize={3}".format(
                        acct.name_, cnt, size, maxsize))
 
            prodFunc = producer.start_flood
            # !!! Throttle param hard coded to 100 for now !!!
            prodArgs = [accountList,transLimit,timelimit,transRate]
  
        # #####################################################################
        # Generate the SFTP jobs from a predefined script
        elif command == "simulate":
            if not vars(args)["actionfile"]:
                logger.critical("Must provide a JSON data file for simulation commands.")
                ap.print_help()
                exit(16)

            prodFunc = producer.start_simulate
            prodArgs = [args.actionfile]
    
        else:
            logger.critical("'{0}' is not a valid run command.".format(command))
            ap.print_help()
            exit(16)
         
        threadCnt = 1
        if command == "flood":
            # Use the supplied worker count, or <system_cpu_cnt>
            threadCnt = multiprocessing.cpu_count() 
            if vars(args)["workercnt"]:
                threadCnt = int(args.workercnt) 

        # #####################################################################
        # Supervise creation & execution of the SFTP jobs 
        with sftp_supervisor(threadCnt, prodFunc, prodArgs, consFunc) as svsr:

            svsr.process_jobs()

            logger.info("Finished processing SFTP jobs.")
            logger.info("\tResults:")
            logger.info("\t========")
            logger.info("\tNumber of SFTP operations sourced:    {0}".format(
                producer.trans_count_))
            logger.info("\tNumber of SFTP operations completed:  {0}".format(
                svsr.complete_count_))
            if svsr.error_count_ > 0:
                logger.info("\tNumber of SFTP operations failed:     {0}".format(
                    svsr.error_count_))
            if svsr.cancel_count_ > 0:
                logger.info("\tNumber of SFTP operations canceled:   {0}".format(
                    svsr.cancel_count_))

        logger.info("SFTP testing complete.")

    except Exception as e:
        msg = "Encountered exception in program __main__: {0}".format(e)
        if logger:
            logger.critical(msg)
        else:
            print(msg)
        exit(32)

