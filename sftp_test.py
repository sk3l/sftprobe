#!/usr/bin/python

from argparse import ArgumentParser 
import sys

from sftp_account import sftp_account

if __name__ == "__main__":

    ap = ArgumentParser(add_help=False)

    ap.add_argument(
        "-a", "--accounts",
        help="FQN of account input JSON file")

    ap.add_argument(
        "-w", "--workercnt",
        help="Number of workers in the thread pool")

    ap.add_argument(
        "-n", "--numlimit", type=int,
        help="Run until <numlimit> transfers hav occurred.")

    ap.add_argument(
        "-t", "--timelimit", type=int,
        help="Run until <timelimit> seconds have elapsed.")

    ap.add_argument("-h", "--help", action='store_true')

    args = ap.parse_args()

    if vars(args)["help"] == True or len(sys.argv) < 2:
        ap.print_help()

   
    accountList = []

    if (vars(args)["accounts"] == True):
        with open(vars(args["accounts"]), "r") as acctf:
           acct = json.load(acctf, object_hook=sftp_account.json_decode)
           while acct != None:
               accountList.append(acct)

            



