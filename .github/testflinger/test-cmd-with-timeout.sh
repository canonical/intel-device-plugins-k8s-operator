#!/bin/bash
#
# Run a command every SLEEP_SECS seconds until it succeeds. 
#
# Passing args to the command is supported, and should NOT
# include surrounding quotes.
#

if [ $# -eq 0 ]; then
    echo "Usage:   $0 <unquoted command to execute>"
    echo "Example: $0 ls -lh"
    exit 1
fi

SLEEP_SECS=30
TIMEOUT_SECS=1800
elapsed_secs=0

# capture all args passed to script and use as the test command
cmd="$*"

while ! ${cmd}; do
  echo "Command '${cmd}' failed, retrying in ${SLEEP_SECS} seconds."
  echo "Elapsed seconds: ${elapsed_secs}"
  sleep ${SLEEP_SECS}
  elapsed_secs=$((elapsed_secs+SLEEP_SECS))
  if (( elapsed_secs > TIMEOUT_SECS )); then
    >&2 echo "Timeout waiting for '${cmd}' to succeed. Exiting."
    exit 1
  fi
done