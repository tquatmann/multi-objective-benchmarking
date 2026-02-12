#!/bin/bash
set -e

echo "This script (re-)builds the docker image for arm and x86."
# Print script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $SCRIPT_DIR

# unzip the source code for storm / modest if not done already
if [ ! -d storm_src ]; then
  unzip storm/storm.zip -d storm_src
fi
if [ ! -d modest_x86 ]; then
  unzip mcsta/modest-linux-x64.zip -d modest_x86
fi
if [ ! -d modest_arm ]; then
  unzip mcsta/modest-linux-arm64.zip -d modest_arm
fi

echo "Start building mopmctools Docker for ARM and x86"
docker buildx build -t mopmctools \
	--build-arg BASE_IMAGE=movesrwth/storm-basesystem:debian-13 --build-arg no_threads=4 \
	--platform linux/arm64,linux/amd64 .
date
echo "Saving docker image $PWD/mopmctools_docker.tar.gz ..."

docker image save mopmctools | gzip > mopmctools_docker.tar.gz
date
