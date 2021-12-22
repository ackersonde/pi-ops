#!/bin/bash

# local cleanup
docker rm -f vault || true
sudo rm -Rf /home/ubuntu/vault/vault_data || true

# remote graceful shutdown and data sync to local disk
ssh -o StrictHostKeyChecking=no ackerson.de docker stop vault
rsync -Pav ackerson.de:/mnt/vault_data/ /home/ubuntu/vault/vault_data/ --delete

/home/ubuntu/vault/backup_restore.sh backup

# spin up local instance for testing sanity of data
#sudo chown -Rf systemd-network:ubuntu /home/ubuntu/vault/vault_data/*

#docker run -d --cap-add=IPC_LOCK -v /home/ubuntu/vault/vault_data:/vault \
#  -e VAULT_API_ADDR=http://127.0.0.1:8200 -e VAULT_ADDR=http://127.0.0.1:8200 \
#  -p 8200:8200 --name vault vault:1.9.1 server
