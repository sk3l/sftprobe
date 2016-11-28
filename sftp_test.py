#!/opt/bb/bin/python3.5

import argparse
import concurrent.futures
import json
import sys
import threading

from sftp_account   import sftp_account
from sftp_consumer  import sftp_consumer
from sftp_producer  import sftp_producer

if __name__ == "__main__":

    try:
        ap = argparse.ArgumentParser(add_help=False)
 
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
            "-s", "--size", type=int,
            help="Size of the transfer input file e.g. 100Kb, 4Mb.")
    
        ap.add_argument(
            "-l", "--sizelimit", type=int,
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
    
        ap.add_argument("-h", "--help", action='store_true')
   
        if len(sys.argv) < 2:
            ap.print_help()
            exit(16)

        args = ap.parse_args()
    
        if vars(args)["help"] == True:
            ap.print_help()
            exit(16)
    
        #workQueue = queue.Queue()   # queue of SFTP tasks
        accountList = []            # list of SFTP test accounts
 
        # Deserialize the account file
        with open(vars(args)["accounts"], "r") as acctf:
            accountList = json.load(acctf, object_hook=sftp_account.json_decode)
           
            for acct in accountList:

                print("Found account '{0}' in input file.".format(acct))
                cnt =   vars(args)["count"]     if vars(args)["count"]      else acct.file_cnt_
                size=   vars(args)["size"]      if vars(args)["size"]       else acct.file_size_
                maxsize=vars(args)["sizelimit"] if vars(args)["sizelimit"]  else acct.file_size_max_
              
                acct.create_data_files("", cnt, size, maxsize)
                
                print("Created data files for account '{0}', count={1}, size={2}, maxsize={3}".format(
                    acct.name_, cnt, size, maxsize))
 
       
        # Use the supplied worker count, or None defaults to <system_cpu_cnt>*5
        threadCnt = None            
        if "workercnt" in vars(args):
            threadCnt = vars(args)["workercnt"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=threadCnt) as threadPool:
            producerTarget = None
            producerArgs   = ()
 
            consumer = sftp_consumer(threadPool)
            producer = sftp_producer(threadPool, consumer.process_job, accountList)       

            # Establish program mode & parameters
            mode = vars(args)["mode"].lower()
            if mode == "random":
                if vars(args)["numlimit"]:
                    transLimit = vars(args)["numlimit"]
                producerTarget = producer.start_random
                producerArgs = (transLimit,)
        
            elif mode == "scripted":
                if not vars(args)["file"]:
                    print("Must provide a script file for --file mode.")
                    ap.print_help()
                    exit(16)
                producerTarget = producer.start_scripted
                producerArgs = (vars(args)["file"],)
        
            else:
                print("'{0}' is not a valid run mode.".format(mode))
                ap.print_help()
                exit(16)
 
            prodThread = threading.Thread(target=producerTarget,args=producerArgs)

            print("Beginning SFTP test data production.")
            prodThread.start()

            prodThread.join()

        print("SFTP testing complete.")

    except Exception as e:
        print("Encountered exception: {0}".format(e))
        exit(32)

