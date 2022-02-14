#!/bin/bash
DATE=`date +"%Y.%m.%d.%Hh%Mm%Ss"`
VAULT_DATA=/home/ubuntu/vault/vault_data
BACKUP_HOST=192.168.178.28
BACKUP_HOME=/mnt/usb4TB/backups/vault-secrets/
MNT_PATH=/mnt/hetzner_disk/vault_data

if ! [[ $# = 2 || $1 =~ ^(backup|restore)$ ]]
then
    echo "Please do request a 'backup' or 'restore' of the Vault data"
    exit 1
else
    if [[ $1 = backup ]]
    then
      echo "Going to backup now..."
      # local cleanup
      docker rm -f vault || true
      sudo rm -Rf $VAULT_DATA || true
      mkdir -p $VAULT_DATA

      docker stop vault || true
      rsync -Pav vault:$MNT_PATH/* $VAULT_DATA --delete

      tar -czf backup-vault_data-$DATE.tgz -C $VAULT_DATA .
      scp backup-vault_data-$DATE.tgz $BACKUP_HOST:$BACKUP_HOME
      rm backup-vault_data-$DATE.tgz
      docker start vault || true
    elif [[ $2 ]]
    then
      FILE=${2/$BACKUP_DIR/} # if restore file contains backup path, remove it (copy/pasta)
      echo "Going to restore $FILE now..."
      exit 1 # not ready to test this yet!
      ssh vault "docker stop vault && sudo rm $MNT_PATH/*"
      scp $BACKUP_HOST:$BACKUP_HOME/$FILE .
      scp $FILE vault:$MNT_PATH
      ssh vault "cd $MNT_PATH; tar -zxvf $MNT_PATH/$FILE; rm $MNT_PATH/$FILE; chown -Rf systemd-network:1000 $MNT_PATH/; docker start vault"
      rm $FILE
    else
      echo "Last 4 backups >15KB in size on vpnpi:"
      ssh $BACKUP_HOST "find $BACKUP_HOME -type f -size +10k -printf '%T@ %p\n' -ls | sort -n | cut -d' ' -f 2 | tail -n 4"
    fi
fi
