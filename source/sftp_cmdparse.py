#!/opt/bb/bin/python3.5

import getpass
import logging
import sys

from sftp_client import sftp_client
from sftp_client import get_sftp_connection

class sftp_cmdparse:

    #logger =  logging.getLogger('sftprobe.cmdparse')
    def __init__(self, addr, user="", pwd="", key=None):
        self.address_ = addr
        self.user_    = user.strip()
        self.password_= pwd.strip()
        self.key_     = key

    def accept_commands(self):
        # Print the command prompt

        if len(self.user_) < 1:
            sys.stdout.write("Enter sftp user name: ")
            sys.stdout.flush()
            self.user_ = sys.stdin.readline().strip()

        if len(self.password_) < 1:
            self.password_ = getpass.getpass()

        with get_sftp_connection(
            self.address_,
            self.user_,
            self.password_,
            self.key_) as conn:

            print(conn.get_status())

            sys.stdout.write("\n$> ")
            for line in sys.stdin:
                try:

                    cmd = line.strip()
                    lcmd= cmd.lower()
                    #sftp_cmdparse.logger.debug(
                    #    "Recevied command '{0}' as input to control mode.".format(cmd))

                    # Parse command and dispatch SFTP command
                    if lcmd.startswith("ls"):
                        path = ""
                        if len(cmd) > 3 and cmd[2] == ' ':
                            path = cmd[3:]

                        listing = conn.do_listdir(path)
                        for item in listing:
                            #sys.stdout.write(attrib)
                            print(item)
                        sys.stdout.flush()

                    elif lcmd.startswith("cd"):
                        path = ""
                        if len(cmd) > 3 and cmd[2] == ' ':
                            path = cmd[3:]

                        conn.do_changedir(path)
                        print("Changed path to '{0}'".format(path))

                    elif lcmd.startswith("get"):

                        if len(lcmd) < 5:
                            print("Missing required remote path for 'get'")
                            continue

                        # Split get args into 'remotePath [localPath]', using
                        # remotePath for the local file path if no localPath
                        # arg is provided.
                        args = lcmd[4:].partition(' ')

                        src = args[0]
                        dest= args[2] if len(args) > 2 and args[2] != "" else src

                        conn.do_get(src, dest)

                        print("Got file '{0}' from remote host to local file '{1}'".format(
                            src,dest))


                    elif lcmd.startswith("put"):

                        if len(lcmd) < 5:
                            print("Missing required local path for 'put'")
                            continue

                        # Split get args into 'localPath [remotePath]', using
                        # localPath for the remote file path if no remotePath
                        # arg is provided.
                        args = lcmd[4:].partition(' ')

                        src = args[0]
                        dest= args[2] if len(args) > 2 and args[2] != "" else src

                        conn.do_put(src, dest)

                        print("Put file '{0}' from local host to remote file '{1}'".format(
                            src,dest))


                    elif lcmd == "quit" or cmd == "bye":
                        print()
                        #sftp_cmdparse.logger.info(
                        #    "Terminating control mode on user's request.")
                        break

                    else:
                        print(
                            ("Sorry, didn't recognize command '{0}'; "
                             "please try again.").format(cmd))

                except Exception as e:
                    print("Error : {0}".format(e))
                finally:
                    if cmd != "quit" and cmd != "bye":
                        sys.stdout.write("$> ")
                        sys.stdout.flush()


