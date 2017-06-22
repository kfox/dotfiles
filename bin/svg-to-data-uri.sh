#!/bin/bash

# brew install svgo

FILENAME=$1
svgo --multipass -i ${1} -o - | \
sed \
  -e "s/\"/'/g" \
  -e 's/</%3C/g' \
  -e 's/>/%3E/g' \
  -e 's/#/%23/g' \
  -e 's/^/data:image\/svg+xml,/'
