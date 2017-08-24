#!/opt/bb/bin/python3.5

import json
import logging
import multiprocessing
import re
import sys
import time

from sftp_argparse      import sftp_argparse
from sftp_account       import sftp_account
from sftp_cmdparse      import sftp_cmdparse
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

log_mod = "sftprobe"

if __name__ == "__main__":

    logger = None
    try:
        ap = sftp_argparse()

        args = ap.parse_args()
        command = args.command

        #######################################################################
        # Read the SFTP commands interactively from stdin
        if command == "control":

            # Turn off logging
            logging.shutdown()
            logger = None

            controller = sftp_cmdparse(args.address)
            controller.accept_commands()

        #######################################################################
        # Using some manner of automated workflow, so prep producer/consumer
        else:
            logger = logging.getLogger(log_mod)

            verbosity = "DEBUG"
            if vars(args)["verbosity"]:
                verbosity = args.verbosity

            logger.setLevel(verbosity)

            formatter = logging.Formatter(
                '%(asctime)s - %(name)s (%(levelname)s) - %(message)s')


            consHandler = logging.StreamHandler()
            consHandler.setLevel(verbosity)
            consHandler.setFormatter(formatter)
            logger.addHandler(consHandler)

            fileHandler = logging.FileHandler(
                            time.strftime("sftprobe_log_%H_%M_%m_%d_%Y.txt"))
            fileHandler.setLevel(verbosity)
            fileHandler.setFormatter(formatter)
            logger.addHandler(fileHandler)

            logger.info(
                "Starting sftprobe as automated task, command='{0}'".format(
                    command))

            # Create the sftp command producer
            producer = sftp_producer()

            prodFunc = None # producer func to produce the commands
            prodArgs   = [] # producer args for command creation

            # Create the sftp command consumer
            consumer = sftp_consumer(args.address)
            consFunc = consumer.process_command

            # #################################################################
            # Randomly generate SFTP commands and send them, in large volume
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
                    accountList = json.load(
                                    acctf, object_hook=sftp_account.json_decode)

                    for acct in accountList:

                        logger.info("Found account '{0}' in input file.".format(
                            acct.name_))

                        cnt = acct.file_cnt_
                        if vars(args)["count"]:
                            cnt = args.count

                        size = acct.file_size_
                        if cliSize > 0:
                            size= cliSize

                        maxsize = acct.file_size_max_
                        if cliMaxSize > 0:
                            maxsize = cliMaxSize

                        if size < 0:
                            logger.warn(
                            ("Encountered bad file size paramter in "
                             "account {0}; skipping.").format(
                                acct.name_))
                            continue
                        elif maxsize <0:
                            logger.warn(
                            ("Encountered bad file maxsize paramter "
                             "in account {0}; skipping.").format(
                                acct.name_))
                            continue

                        acct.create_data_files("", cnt, size, maxsize)

                        logger.info(
                            ("Created data files for account '{0}', "
                             "count={1}, size={2}, maxsize={3}").format(
                            acct.name_, cnt, size, maxsize))

                prodFunc = producer.start_flood
                prodArgs = [accountList,transLimit,timelimit,transRate]

            # #################################################################
            # Read the SFTP commands from a predefined script
            elif command == "trace":
                if not vars(args)["cmdfile"]:
                    logger.critical(
                        "Must provide a JSON data file for trace commands.")
                    ap.print_help()
                    exit(16)

                prodFunc = producer.start_trace
                prodArgs = [args.cmdfile]

            else:
                logger.critical(
                    "'{0}' is not a valid run command.".format(command))
                ap.print_help()
                exit(16)

            workerCnt = 1
            if command == "flood":
                # Use the supplied worker count, or <system_cpu_cnt>
                workerCnt = multiprocessing.cpu_count()
                if vars(args)["workercnt"]:
                    workerCnt = int(args.workercnt)

            # #################################################################
            # Supervise execution of the SFTP commands
            with sftp_supervisor(workerCnt, prodFunc, prodArgs, consFunc) as s:

                s.execute_commands()

                logger.info("Finished processing SFTP commands.")
                logger.info("\tResults:")
                logger.info("\t========")
                logger.info(
                    "\tNumber of SFTP operations sourced:    {0}".format(
                    producer.trans_count_))
                logger.info(
                    "\tNumber of SFTP operations completed:  {0}".format(
                    s.complete_count_))
                if s.error_count_ > 0:
                    logger.info(
                        "\tNumber of SFTP operations failed:     {0}".format(
                        s.error_count_))
                if s.cancel_count_ > 0:
                    logger.info(
                        "\tNumber of SFTP operations canceled:   {0}".format(
                        s.cancel_count_))

            logger.info("SFTP testing complete.")

    except Exception as e:
        msg = "Encountered exception in program __main__: {0}".format(e)
        if logger:
            logger.critical(msg)
        else:
            print(msg)

        exit(32)

    finally:
        if logger:
            logging.shutdown()

