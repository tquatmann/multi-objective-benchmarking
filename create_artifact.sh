#!/bin/bash

zip -r $1 \
  artifact/LICENSE \
  artifact/README.md \
  artifact/experiments/all.json \
  artifact/experiments/large.json \
  artifact/experiments/medium.json \
  artifact/experiments/small.json \
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
  artifact/tools/run_docker.sh

du -h $1