#!/bin/bash

#set -xe
set -x

if [ -f /etc/raas/initialized ]
then
  raas "$@"
else
  # this line should move away from hard coded values and instead use environment variables that can be set in the compose file
  /usr/bin/raas save_creds 'postgres={"username": "default", "password": "postgres123"}' 'redis={"username": "default", "password": "redis123"}'
  # allow an initial raas run of 60s, to allow for instantiating the postgres db, then kill it
  #timeout 60 raas "$@"
  raas "$@" &
  sleep 60
  # we cannot set 'set -e' earlier as the timeout command above is expected to return a non zero exit code, but we need to catch the raas dump if it fails to prevent the initialization flag from being a false positive
  set -e
  # this should import the initial content for raas
  bash -c "/usr/bin/raas dump --insecure --server http://localhost:8080 --auth root:salt --mode import < /tmp/sample-resource-types.raas"
  # set flag to go straight to raas run on subsequent starts
  touch /etc/raas/initialized
  # run raas normally once init is completed
  #raas "$@"
fi