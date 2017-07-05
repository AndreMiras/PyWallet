#!/bin/bash

# exits on fail
set -e

source travis/tools.sh
# start the ping loop
ping_loop
# start the buildozer build
buildozer android debug >> $BUILD_OUTPUT 2>&1
# the build finished without returning an error so dump a tail of the output
dump_output
# nicely terminate the ping output loop
kill $PING_LOOP_PID
