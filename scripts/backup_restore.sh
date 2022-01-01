#!/bin/bash
DATE=`date +"%Y.%m.%d.%Hh%Mm%Ss"`
VAULT_HOME=/home/ubuntu/vault/vault_data
BACKUP_HOST=192.168.178.28
BACKUP_HOME=/mnt/usb4TB/backups/vault-secrets/
MNT_PATH=/mnt/vault_data

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
      sudo rm -Rf $VAULT_HOME || true
      mkdir -p $VAULT_HOME

      # remote graceful shutdown and data sync to local disk
      ssh -o StrictHostKeyChecking=no ackerson.de "docker stop vault"
      rsync -Pav ackerson.de:$MNT_PATH $VAULT_HOME --delete
      ssh ackerson.de "umount $MNT_PATH"

      tar -czf backup-vault_data-$DATE.tgz -C $VAULT_HOME .
      scp backup-vault_data-$DATE.tgz $BACKUP_HOST:$BACKUP_HOME
      rm backup-vault_data-$DATE.tgz
    elif [[ $2 ]]
    then
      FILE=${2/$BACKUP_DIR/} # if restore file contains backup path, remove it (copy/pasta)
      echo "Going to restore $FILE now..."
      exit 1 # not ready to test this yet!
      ssh ackerson.de "docker stop vault && sudo rm $MNT_PATH/*"
      scp 192.168.178.28:$BACKUP_HOME/$FILE .
      scp $FILE ackerson.de:$MNT_PATH
      ssh ackerson.de "cd $MNT_PATH; tar -zxvf $MNT_PATH/$FILE; rm $MNT_PATH/$FILE; docker start vault"
      rm $FILE
    else
      echo "Last 10 backups >15KB in size on vpnpi:"
      ssh $BACKUP_HOST "find $BACKUP_HOME -type f -size +10k -printf '%T@ %p\n' -ls | sort -n | cut -d' ' -f 2 | tail -n 10 | xargs -r ls -l"
    fi
fi
