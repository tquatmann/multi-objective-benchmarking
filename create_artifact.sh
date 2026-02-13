#!/bin/bash

# check if $1 is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <output_zip_file>"
  exit 1
fi
zip -r $1 \
  artifact/LICENSE \
  artifact/README.md \
  artifact/experiments/all.json \
  artifact/experiments/subset-large.json \
  artifact/experiments/subset-medium.json \
  artifact/experiments/subset-small.json \
  artifact/paper_results/ \
  artifact/qcomp/ \
  artifact/quickcheck/inv.json \
  artifact/quickcheck/run.sh \
  artifact/scripts/data/*.json \
  artifact/scripts/internal/*.py \
  artifact/scripts/internal/*.json \
  artifact/scripts/internal/*.tex \
  artifact/scripts/*.py \
  artifact/tools/Dockerfile \
  artifact/tools/build_docker.sh \
  artifact/tools/storm/ \
  artifact/tools/mcsta/ \
  artifact/tools/mopmctools_docker.tar.gz \
  artifact/run_docker.sh

du -h $1
md5 $1