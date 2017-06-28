#!/bin/bash
# Android specific Travis script

# exits on fail
set -e

sudo pip install --install-option="--no-cython-compile" cython==0.21
sudo pip install --upgrade buildozer
./travis/buildozer_android.sh
