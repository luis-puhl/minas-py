#!/bin/sh
# compare $1 $2 -compose src diff.png
compare $2 $1 png:- | montage -geometry +4+4 $2 - $1 png:- | display -title "$1" -
