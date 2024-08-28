#!/bin/bash

# Set up a named pipe for the communication between
# the application and stdout-redirect
rm /tmp/fifo 2>/dev/null
mkfifo /tmp/fifo
## Spawn stdout-redirect with the named pipe as input
(
  exec &>/dev/null # Ignore the output of stdout-redirect if there is any
  /stdout-redirect -logfile=/logs/app.log -format=json -size=10 -rotate=10 -redirect=all </tmp/fifo &
)

# Copy the stdout and stderr streams of the application to the named pipe
exec &> >(
  tee -i /tmp/fifo
)

# Replace the current process with the application
exec "$@"