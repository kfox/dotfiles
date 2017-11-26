#!/usr/bin/env bash

PICTURE_DIR="$HOME/Pictures/Bing"

mkdir -p $PICTURE_DIR

urls=( $(curl -s http://www.bing.com 2>/dev/null | \
  grep -Eo "url:'.*?'" | \
  sed -e "s/url:'\([^']*\)'.*/http:\/\/bing.com\1/" | \
  sed -e "s/\\\//g") )

for p in ${urls[@]}; do
  filename=$(echo $p|sed -e "s/.*\/\(.*\)/\1/")
  fullpath=$PICTURE_DIR/$filename
  if [ ! -f "${fullpath}" ]; then
    curl -s -Lo "$fullpath" $p
    /usr/bin/osascript -e "tell application \"Finder\" to set desktop picture to POSIX file \"$fullpath\""
  fi
done
