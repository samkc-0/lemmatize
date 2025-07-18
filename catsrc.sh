#!/bin/bash

# get git-tracked + untracked files, excluding ignored ones and uv.lock
files=$(git ls-files --others --cached --exclude-standard | grep -v '^uv\.lock$')

for f in $files; do
  if [ -f "$f" ]; then
    echo "===== $f ====="
    cat "$f"
    echo
  fi
done