#!/opt/bb/bin/python3.5

import argparse
import sys

class sftp_argparse():

    title_ = ("\nsftprobe - an SFTP server test tool\n") 

    desc = (
            "usage: sftprobe.py command\n\n"
            "    command:\n"
            "           flood - saturate an SFTP server "
                        "with randomly generated traffic\n"
            "        trace - execute a series of SFTP commands from a file\n\n"
            "type 'sftprobe help <cmd>' for command-specific help\n\n"
            )


    def __init__(self):
        self.parser_ = argparse.ArgumentParser()

        self.cmdparsers_ = self.parser_.add_subparsers()

        self.helpparser_ = self.cmdparsers_.add_parser("help")

        self.flood_parser_ = self.cmdparsers_.add_parser("flood", 
                description="    Saturate an SFTP server with randomly generated traffic\n")

        self.flood_parser_.add_argument("address",
            help="Address of server to test against e.g. localhost:22.")

        self.flood_parser_.add_argument("accounts",
            help="FQN of account input JSON file")
 
        self.flood_parser_.add_argument(
            "-c", type=int, dest="count", metavar="count",
            help="Number of test account files to transfer.")

        self.flood_parser_.add_argument(
            "-s", dest="size",  metavar="size",
            help="Size of the random transfer input file e.g. 100Kb, 4Mb.")

        self.flood_parser_.add_argument(
            "-m", dest="maxsize", metavar="maxsize",
            help="Max size for random transfer input file e.g. 100Kb, 4Mb.")
 
        self.flood_parser_.add_argument(
            "-r", type=int, dest="rate", metavar="rate",
            help="Max number of transfers to generate per second")

        self.flood_parser_.add_argument(
            "-n", type=int, dest="numlimit", metavar="numlimit",
            help="Run until <numlimit> transfers hav occurred.")
   
        self.flood_parser_.add_argument(
            "-t", type=int, dest="timelimit", metavar="timelimit",
            help="Run until <timelimit> seconds have elapsed.")

        self.flood_parser_.add_argument(
            "-w", dest="workercnt", metavar="workercnt",
            help="Number of workers in thread pool (defaults to machine CPU count)")
 
        self.flood_parser_.add_argument(
            "-v", dest="verbosity", metavar="verbosity",
            help="Verbosity level for Python Logging framework (default=DEBUG)")

        self.trace_parser_ = self.cmdparsers_.add_parser(
                "trace",
                description="    Execute a sequence of SFTP commands from a file\n")

        self.trace_parser_.add_argument("address",
            help="Address of server to test against e.g. localhost:22.")

        self.trace_parser_.add_argument(
            "actionfile", metavar="actionfile",
            help="FQN of JSON file containing trace actions.")

        self.trace_parser_.add_argument(
            "-v", dest="verbosity", metavar="verbosity",
            help="Verbosity level for Python Logging framework (default=DEBUG)")

    # Pass-through to internal argparse.ArgumentParser
    def parse_args(self):

        argc = len(sys.argv)
        if argc < 2:
            print(sftp_argparse.title_)
            print(sftp_argparse.desc)
            exit(1)

        cmd = sys.argv[1].lower()
        if cmd == "help" or argc < 3:
            print(sftp_argparse.title_)

            helpcmd = sys.argv[2].lower() if argc > 2 else ""

            if  cmd == "flood" or helpcmd == "flood" :
                self.flood_parser_.print_help()
                exit(1)
            elif cmd == "trace" or helpcmd == "trace":
                self.trace_parser_.print_help()
                exit(1)
            else:
                if cmd != "help":
                    print("Unrecognized command '{0}'\n".format(cmd))
                elif helpcmd != "":
                    print("Unrecognized command '{0}'\n".format(helpcmd))
                print(sftp_argparse.desc)
                exit(1)

        else:
            self.args = self.parser_.parse_args()

            vars(self.args)["command"] = cmd
            return self.args

