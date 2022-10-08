#!/bin/bash
if [[ $(cat ~/homepage_host_key | awk '{print $3}') == "$(ssh-keyscan -t ed25519 ackerson.de | awk '{print $3}')" ]]; then
  ssh-keygen -R ackerson.de && ssh-keyscan -H ackerson.de >> ~/.ssh/known_hosts
else
  echo "$(date) -- SSH host key for ackerson.de does NOT match"
fi
