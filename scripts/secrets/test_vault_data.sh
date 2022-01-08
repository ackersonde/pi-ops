#!/bin/bash
# spin up local instance for testing sanity of data
sudo chown -Rf systemd-network:ubuntu /home/ubuntu/vault/vault_data/*

docker run -d --cap-add=IPC_LOCK -v /home/ubuntu/vault/vault_data:/vault \
  -e VAULT_API_ADDR=http://127.0.0.1:8200 -e VAULT_ADDR=http://127.0.0.1:8200 \
  -p 8200:8200 --name vault vault:1.9.1 server
