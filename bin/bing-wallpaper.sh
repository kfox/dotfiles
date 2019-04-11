#!/usr/bin/env bash

PICTURE_DIR="$HOME/Google Drive/Pictures/Bing"

mkdir -p "$PICTURE_DIR"

url="$(curl -s http://www.bing.com 2>/dev/null | \
  grep -Eo "url:'.*?'" | \
  head -1 |
  sed -e "s/url:'\([^']*\)'.*/http:\/\/bing.com\1/" -e "s/\\\//g")"


filename=$(echo "$url" | sed 's/.*\/th.id=OHR.\([^&]*\)\&amp.*/\1/' )
fullpath=$PICTURE_DIR/$filename
if [ ! -f "${fullpath}" ]; then
  curl -s -Lo "$fullpath" "$url"
  /usr/bin/osascript -e \
    "tell application \"Finder\" to set desktop picture to POSIX file \"$fullpath\"" \
    >/dev/null 2>&1
fi
