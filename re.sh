#!/bin/bash

PROJECT_DIR=$(pwd)

echo "Listing files and directories in the project folder (ignoring .git folder):"
echo "---------------------------------------------------------------------------"
find "${PROJECT_DIR}" -type d -name '.git' -prune -o -type d -o -type f -print | sed 's|^./||'
bash