#!/bin/bash
DATE=`date +"%Y.%m.%d.%Hh%Mm%Ss"`

if ! [[ $# = 2 || $1 =~ ^(backup|restore)$ ]]
then
    echo "Please do request a 'backup' or 'restore' of the Vault data"
    exit 1
else
    if [[ $1 = backup ]]
    then
      echo "Going to backup now..."
      tar -czf backup-vault_data-$DATE.tgz -C /home/ubuntu/vault vault_data
      scp backup-vault_data-$DATE.tgz 192.168.178.28:/mnt/usb4TB/backups/vault-secrets/
      rm backup-vault_data-$DATE.tgz
    elif [[ $2 ]]
    then
      FILE=${2/$BACKUP_DIR/} # if restore file contains backup path, remove it (copy/pasta)
      echo "Going to restore $FILE now..."
      ssh ackerson.de docker stop vault
      scp $BACKUP_HOST:$BACKUP_DIR/$FILE ackerson.de:$MNT_PATH
      ssh ackerson.de tar -zxvf $MNT_PATH
      docker start vault
      rm $FILE
    else
      echo "Last 10 backups >15KB in size on vpnpi:"
      ssh $BACKUP_HOST "find $BACKUP_DIR -type f -size +15k -printf '%T@ %p\n' -ls | sort -n | cut -d' ' -f 2 | tail -n 10 | xargs -r ls -l"
    fi
fi
