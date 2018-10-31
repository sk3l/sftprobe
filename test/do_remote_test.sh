#!/bin/bash

APP=../source/sftprobe.py
ACCT="$1"
SERVER="$2:$3"
#ACCT=./accounts.cisftpdev.json
FILECNT=100
WORKERS=10
RATE=100
TIME=60
LOGLVL=INFO

# teardown from previous tests


echo "Cleaning up from previou tests"
#sudo truncate -s 0 /var/log/sftp.log

#if [ -e ~tesla ]; then
#   sudo rm -f ~tesla/test*
#fi

if [ ! -e /tmp/data ]; then
   mkdir /tmp/data
fi

rm -f ~/tmp/*

echo "Running sftp test app"
$APP flood $SERVER $ACCT -c $FILECNT -t $TIME -w $WORKERS -r $RATE -v $LOGLVL #> /dev/null 2>&1

# cleanup
echo "Back up test logs"
if ls ./sftprobe_log* > /dev/null 2>&1; then
   cat ./sftprobe_log*
   mv ./sftprobe_log* ./logs
fi
#cp /var/log/sftp.log "./logs/sftp.log.$(date -Iseconds)"

#sudo cp /var/log/sftp.log "./logs/sftp.log.$(date -Iseconds)"
#sudo chown mskelton8:mskelton8 logs/sftp.log*
