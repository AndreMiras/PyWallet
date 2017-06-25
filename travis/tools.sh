#!/bin/bash
# https://stackoverflow.com/a/26082445/185510
# Quick example how to use this file:
: <<'END'
# source this file before using:
source tools.sh

# start the ping loop
ping_loop

# then execute your_build_command_1 with redirect:
your_build_command_1 >> $BUILD_OUTPUT 2>&1
your_build_command_2 >> $BUILD_OUTPUT 2>&1

# the build finished without returning an error so dump a tail of the output:
dump_output

# nicely terminate the ping output loop
kill $PING_LOOP_PID
END

export PING_SLEEP=30s
export WORKDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export BUILD_OUTPUT=$WORKDIR/build.out

touch $BUILD_OUTPUT

dump_output() {
   echo Tailing the last 500 lines of output:
   tail -500 $BUILD_OUTPUT
}
error_handler() {
  echo ERROR: An error was encountered with the build.
  dump_output
  kill $PING_LOOP_PID
  exit 1
}
# if an error occurs, run our error handler to output a tail of the build
trap 'error_handler' ERR

ping_loop() {
  # set up a repeating loop to send some output to Travis.
  bash -c "while true; do echo \$(date) - building ...; sleep $PING_SLEEP; done" &
  PING_LOOP_PID=$!
}
