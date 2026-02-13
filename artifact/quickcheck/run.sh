#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR
echo "Directory of script is $PWD"
rm -rf logs/*

python3 ../scripts/run.py inv.json
echo "mcsta output:"
grep -A4 "+ multi" logs/*
echo "Storm output:"
grep -A3 Result logs/*
