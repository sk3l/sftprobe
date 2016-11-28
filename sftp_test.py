#!/usr/bin/python

import json
from argparse import ArgumentParser 
import sys

from sftp_account import sftp_account

runMode = None

if __name__ == "__main__":

    ap = ArgumentParser(add_help=False)

    ap.add_argument(
        "-a", "--accounts",
        help="FQN of account input JSON file")

    ap.add_argument(
        "-w", "--workercnt",
        help="Number of workers in the thread pool (defaults to machine CPU core count)")

    ap.add_argument(
        "-m", "--mode",
        help="Mode of operation: choices are 'random' or 'scripted'.")

    ap.add_argument(
        "-n", "--numlimit", type=int,
        help="Run until <numlimit> transfers hav occurred.")

    ap.add_argument(
        "-t", "--timelimit", type=int,
        help="Run until <timelimit> seconds have elapsed.")
    
    ap.add_argument(
        "-s", "--scriptfile",
        help="FQN of input script file.")

    ap.add_argument("-h", "--help", action='store_true')

    args = ap.parse_args()

    if vars(args)["help"] == True or len(sys.argv) < 2:
        ap.print_help()

    accountList = []

    if (vars(args)["accounts"]):
        with open(vars(args)["accounts"], "r") as acctf:
           accountList = json.load(acctf, object_hook=sftp_account.json_decode)
           print(accountList)

    if (vars(args)["mode"]):
        mode = vars(args)["mode"].lower()
        if mode == "random":
            runMode = 'R'
        elif mode == "scripted":
            runMode = 'S'
        else:
            print("'{0}' is not a valid run mode.".format(mode))
            ap.print_help()
            exit(16)
            



