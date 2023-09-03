#!/bin/bash

#set -xe
set -x

if [ ! -f /etc/raas/initialized ]
then
  # this line should move away from hard coded values and instead use environment variables that can be set in the compose file
  /usr/bin/raas save_creds 'postgres={"username": "default", "password": "postgres123"}' 'redis={"username": "default", "password": "redis123"}'
  # start raas and wait 60 seconds before continuing to allow the DB to be initialized
  raas "$@" &
  sleep 60
  # we cannot set 'set -e' earlier as the timeout command above is expected to return a non zero exit code, but we need to catch the raas dump if it fails to prevent the initialization flag from being a false positive
  set -e
  # this should import the initial content for raas
  bash -c "/usr/bin/raas dump --insecure --server http://localhost:8080 --auth root:salt --mode import < /tmp/sample-resource-types.raas"
  # set flag to go straight to raas run on subsequent starts
  touch /etc/raas/initialized
  pkill raas
fi

# run raas with all passed options
raas "$@"