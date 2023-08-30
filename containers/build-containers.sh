#!/bin/bash

# Check if the user has requested help
if [[ "$1" == "-h" || "$1" == "--help" ]]
then
	# Print usage information
	echo "Usage: $0 [OPTIONS] [TAR_FILE] [VERSION]

Builds Docker images for Aria Automation Config

OPTIONS:
	--clean   Remove all unpacked installer directories.

TAR_FILE:
	Path to the installer bundle to use when building images.

VERSION:
	Optional version tag to apply to the images. If not specified, the tag \"latest\" will be used.

Examples:
	$0 ./ARIA_AUTOMATION_CONFIG.tar 8.13.0
	$0 --clean"
	exit 0
fi

# Enable verbose output and exit on error
set -xe

# Check if the user has requested to clean up unpacked installer directories
echo "Cleaning the following files:"
rm -rfv ./sse-installer ./raas/eapi_service ./salt-master/eapi_plugin
if [[ $1 == "--clean" ]]
then
	exit 0
fi

# Extract the installer bundle
tar xvf $1

# Copy the installers to build directories
cp -rv ./sse-installer/salt/sse/eapi_service ./raas/
cp -rv ./sse-installer/salt/sse/eapi_plugin ./salt-master

# Build the raas image
cd ./raas
FILE_PATH=$(ls eapi_service/files/raas*.rpm)
FILE_NAME=$(basename $FILE_PATH)
if [ -z "$2" ]
then
	# If no version tag is specified, tag the image as "latest"
	docker build . -t "raas:latest" --platform linux/amd64 --build-arg filename=$FILE_NAME
else
	# If a version tag is specified, tag the image as "latest" and with the specified tag
	docker build . -t "raas:latest" -t "raas:$2" --platform linux/amd64 --build-arg filename=$FILE_NAME
fi
cd ..

# Build the salt-master image
cd ./salt-master
SALT_VERSION="3004.2"
PLUGIN_PATH=$(ls eapi_plugin/files/SSEAPE*.whl)
PLUGIN_NAME=$(basename $PLUGIN_PATH)
if [ -z "$2" ]
then
	# If no version tag is specified, tag the image as "latest"
	docker build . -t "salt-master:latest" --build-arg plugin_name=$PLUGIN_NAME --build-arg salt_version=$SALT_VERSION
else
	# If a version tag is specified, tag the image as "latest" and with the specified tag
	docker build . -t "salt-master:latest" -t "salt-master:$2" --build-arg plugin_name=$PLUGIN_NAME --build-arg salt_version=$SALT_VERSION
fi