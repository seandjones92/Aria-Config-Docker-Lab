#!/bin/bash

docker compose down
rm -rf data/postgres/*
rm -rf data/raas/pki/
rm -rf data/raas/raas.secconf
rm -rf data/raas/initialized
rm -rf data/master/pki/
rm -rf data/redis/redis.conf