#!/bin/bash

docker run --rm -it -v ./raas/:/etc/raas raas:latest save_creds
