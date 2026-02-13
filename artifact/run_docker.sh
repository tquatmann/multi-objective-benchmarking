#!/bin/bash
set -e

# Print script directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "Directory of script is $SCRIPT_DIR"

# Print Docker version
docker -v

# ensure that directories are present
mkdir -p "$SCRIPT_DIR/quickcheck/logs"
mkdir -p "$SCRIPT_DIR/experiments/logs"
mkdir -p "$SCRIPT_DIR/bin"

# create symlinks for modest and storm
if [ ! -L "$SCRIPT_DIR/bin/modest" ]; then
  if [[ $(uname -m) == arm* ]]; then
    echo "Detected ARM architecture. Using modest for ARM."
    ln -sf "/opt/modest_arm/Modest/modest" "$SCRIPT_DIR/bin/modest"
  else
    echo "Detected x86 architecture. Using modest for x86."
    ln -sf "/opt/modest_x86/Modest/modest" "$SCRIPT_DIR/bin/modest"
  fi
fi
if [ ! -L "$SCRIPT_DIR/bin/storm" ]; then
  ln -sf "/opt/storm/build/bin/storm" "$SCRIPT_DIR/bin/storm"
fi
# Check whether containerd image store is loaded. Otherwise inform the user.
if [ -z "$(docker info -f '{{ .DriverStatus }}' | grep containerd 2> /dev/null)" ]; then
	echo "Could not detect whether containerd image store is enabled."
	echo "In the Docker settings, make sure that the 'Use containerd for pulling and storing images' option is enabled."
	echo "This is necessary to support the provided multi-platform image, see https://docs.docker.com/build/building/multi-platform/."
  read -p "Continue anyway? (Y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 255
fi

# Check whether mopmctools image is loaded. Load if necessary.
if [ -z "$(docker images -q mopmctools 2> /dev/null)" ]; then
	echo "Loading Docker image."
	docker load -i "$SCRIPT_DIR/tools/mopmctools_docker.tar.gz"
fi

# Run docker
echo ""
echo "Running mopmctools Docker container."
echo "Type 'exit' to exit from docker..."
docker run --rm -v "$SCRIPT_DIR/:/opt/artifact" -w "/opt/artifact" -it mopmctools bash -c "\
  /opt/artifact/bin/modest mcsta | grep version;
  /opt/artifact/bin/storm;
  exec /bin/bash"
