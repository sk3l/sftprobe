#!/bin/bash

APP=../source/sftp_test.py
SERVER=localhost
MODE=random
ACCT=./accounts.tester.json
FILECNT=100
WORKERS=14
TIME=60
LOGLVL=INFO

# teardown from previous tests
echo "Cleaning up from previou tests"
sudo truncate -s 0 /var/log/sftp.log
sudo rm -f ~tester/Test*
rm -f ~/tmp/*

echo "Running sftp test app"
$APP -s $SERVER -m $MODE -a $ACCT -c $FILECNT -t $TIME -w $WORKERS -v $LOGLVL > /dev/null 2>&1

# cleanup
echo "Back up test logs"
if [ -e ./sftp_test_log* ]; then
   cat ./sftp_test_log*
   mv ./sftp_test_log* ./logs
fi
cp /var/log/sftp.log "./logs/sftp.log.$(date -Iseconds)"

