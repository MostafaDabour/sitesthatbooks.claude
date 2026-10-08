#!/usr/bin/env bash
# Rebuilds the live site into ./site from the generator in ./src
set -e
cd "$(dirname "$0")/src"
python3 build.py deploy
rm -rf ../site
mv dist ../site
echo "Built into ./site"
