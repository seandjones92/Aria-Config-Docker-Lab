#!/bin/bash

docker compose up postgres -d
docker compose up redis -d
docker run --rm -it -v ./raas/:/etc/raas raas:latest save_creds
docker run --rm -it -v ./raas/:/etc/raas raas:latest "dump --insecure --mode import < /tmp/sample-resource-types.raas"
docker compose up -d