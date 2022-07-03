#!/bin/bash
HOST=https://vault.ackerson.de
FILE=/home/ubuntu/.netrc

if [[ -n $1 ]]; then
  HOST=$1
fi

if [[ -f $FILE && -f /usr/bin/jq ]]; then
    echo "Checking if $HOST is sealed..."
    sealed=$(curl -s -n "$HOST/v1/sys/seal-status" | jq .sealed)
    echo $sealed
    if [[ $sealed == true ]]; then
      curl -s -n -X POST --data @/home/ubuntu/.unsealKey1 $HOST/v1/sys/unseal
      curl -s -n -X POST --data @/home/ubuntu/.unsealKey2 $HOST/v1/sys/unseal
    fi
else
    echo "ERR: $FILE or jq doesn't exist - can't authenticate to vault.ackerson.de..."
fi
