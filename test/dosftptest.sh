#!/bin/bash

APP=../source/sftprobe.py
SERVER=localhost
ACCT=./accounts.tester.json
FILECNT=100
WORKERS=12
TIME=30
LOGLVL=INFO

# teardown from previous tests
echo "Cleaning up from previou tests"
sudo truncate -s 0 /var/log/sftp.log

if [ -e ~tester ]; then
   sudo rm -f ~tester/test*
fi

if [ -e ~tester2 ]; then
   sudo rm -f ~tester2/test*
fi

rm -f ~/tmp/*

echo "Running sftp test app"
$APP flood $SERVER $ACCT -c $FILECNT -t $TIME -w $WORKERS -r 200 -v $LOGLVL > /dev/null 2>&1

# cleanup
echo "Back up test logs"
if ls ./sftp_test_log* > /dev/null 2>&1; then
   cat ./sftp_test_log*
   mv ./sftp_test_log* ./logs
fi
cp /var/log/sftp.log "./logs/sftp.log.$(date -Iseconds)"

sudo cp /var/log/sftp.log "./logs/sftp.log.$(date -Iseconds)"
#sudo chown mskelton8:mskelton8 logs/sftp.log*
