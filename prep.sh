#!/bin/bash

# Help output for this script
function help() {
	echo "Usage: prep.sh [OPTIONS] INSTALLER_BUNDLE"
	echo "Extracts the installer bundle and prepares the build directories."
	echo ""
	echo "Options:"
	echo "  --clean  Clean up build dirs"
	echo "  --help   Display this help message."
}

if [[ $1 == "--help" ]]
then
	help
	exit 0
fi

# clean the build dirs before every build prep
rm -rf ./build/sse-installer ./build/raas/eapi_service ./build/salt-master/eapi_plugin .env

# Check if the user has requested to only clean up unpacked installer directories
# if we are cleaning only then stop here and don't unpack again
if [[ $1 == "--clean" ]]
then
	exit 0
fi

# Extract the installer bundle
tar zxf vRA_SaltStack_Config*.tar.gz -C build # TODO: add ability to handle tar.gz

# Copy the installers to build directories
cp -r ./build/sse-installer/salt/sse/eapi_service ./build/raas/
cp -r ./build/sse-installer/salt/sse/eapi_plugin ./build/salt-master

# build the .env file
RAAS_FILE_PATH=$(ls build/raas/eapi_service/files/raas*.rpm)
RAAS_FILE_NAME=$(basename $RAAS_FILE_PATH)
echo "RAAS_RPM_NAME=$RAAS_FILE_NAME" >> .env

MASTER_PLUGIN_PATH=$(ls build/salt-master/eapi_plugin/files/SSEAPE*.whl)
MASTER_PLUGIN_NAME=$(basename $MASTER_PLUGIN_PATH)
echo "MASTER_PLUGIN_NAME=$MASTER_PLUGIN_NAME" >> .env
echo "POSTGRES_USER=default" >> .env
echo "POSTGRES_PASS=postgres123" >> .env
echo "REDIS_PASS=redis123" >> data/redis/redis.conf
