#!/bin/bash

CONSUL_SERVER=`docker ps --format '{{.Names}}' | grep secrets_server\\\\. | awk 'NR==1{print $1}'`
DATE=`date +"%Y.%m.%d.%Hh%Mm%Ss"`

if ! [[ $# = 2 || $1 =~ ^(backup|restore)$ ]]
then
    echo "Please do request a 'backup' or 'restore' of the Consul DB"
    exit 1
else
    if [[ $1 = backup ]]
    then
      echo "Going to backup now..."
      docker exec -i $CONSUL_SERVER consul snapshot save backup-$DATE.snap
      docker cp $CONSUL_SERVER:backup-$DATE.snap .
      scp backup-$DATE.snap 192.168.178.28:/mnt/usb4TB/backups/consul-vault-secrets/
      rm backup-$DATE.snap
    elif [[ $2 ]]
    then
      VAULT_SEALED=`curl -s http://pi4:8200/v1/sys/seal-status | jq '.sealed'`
      if ! $VAULT_SEALED; then echo "Vault not sealed. Aborting..." && exit 2; fi
      echo "Going to restore now..."
      scp 192.168.178.28:/mnt/usb4TB/backups/consul-vault-secrets/$2 .
      docker cp $2 $CONSUL_SERVER:backup.snap
      docker exec -it $CONSUL_SERVER consul snapshot restore backup.snap
    else
      echo "Please provide backup file to restoration cmd"
      exit 1
    fi
fi
