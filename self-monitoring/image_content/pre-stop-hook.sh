#!/bin/sh
sigterm_handler() {
    echo "Received SIGTERM, shutting down immediately"
    kill -9 "$tail_pid"
    exit 0
}
trap 'sigterm_handler' SIGTERM
tail -f /dev/null &
tail_pid=$!
wait "$tail_pid"