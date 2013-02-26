#!/bin/bash

if [ $# -lt 1 ]; then
  if [ -t 0 ]; then
    echo "Usage $0 pamfile"
    echo "Usage cat pamfile | $0"
    exit 1
  else
    IN="/dev/stdin"
  fi
else
  IN="$1"
fi

cat "$IN" | tr '\n' ' ' | tr '\r' ' ' | sed 's/<xhtml:body\/>/<xhtml:body>No abstract.<\/xhtml:body>/g' | grep -oP '<dc:title>[^<]+</dc:title>.*?<xhtml:body>.*?</xhtml:body>' | sed "s/\"/'/g;s/<dc:title>\(.*\)<\/dc:title>.*<xhtml:body>\(.*\)<\/xhtml:body>/{\"title\":\"\1\",\"abstract\":\"\2\"}/g"
