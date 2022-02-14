#!/bin/bash
# spin up local instance for testing sanity of data
sudo chown -Rf systemd-network:ubuntu /home/ubuntu/vault/vault_data/*

docker run -d --cap-add=IPC_LOCK \
  -v /home/ubuntu/vault/vault_data:/vault \
  -e VAULT_API_ADDR=http://127.0.0.1:8200 \
  -e VAULT_ADDR=http://127.0.0.1:8200 \
  --label='traefik.enable=true' \
  --label='traefik.http.routers.vault.middlewares=http-ratelimit@file,secHeaders@file,api_auth' \
  --label='traefik.http.routers.vault.tls.certResolver=letsencrypt' \
  --label='traefik.http.routers.vault.tls.domains=hv.ackerson.de' \
  --label='traefik.http.routers.vault.rule=Host(`hv.ackerson.de`)' \
  --name vault vault:latest server
