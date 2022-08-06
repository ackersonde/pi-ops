#!/bin/bash
WORKING_DIR=/home/ubuntu/my-ca
GITHUB_DEPLOY_KEY_FILE=~/.ssh/github_deploy_params
if [ -s "$GITHUB_DEPLOY_KEY_FILE" ]; then
    source $GITHUB_DEPLOY_KEY_FILE
else
    echo "$GITHUB_DEPLOY_KEY_FILE required. No params == no run."
    exit
fi
export GITHUB_SECRETS_PK_PEM=$(cat $GITHUB_SECRETS_PK_PEM_FILE)
VAULT_UPDATE_GITHUB_FILE=~/.ssh/vault_update_github_params
if [ -s "$VAULT_UPDATE_GITHUB_FILE" ]; then
    source $VAULT_UPDATE_GITHUB_FILE
else
    echo "$VAULT_UPDATE_GITHUB_FILE required. No params == no run."
    exit
fi

# shutdown and backup Vault offsite
/home/ubuntu/vault/backup_restore.sh backup

mkdir -p $WORKING_DIR/archive
mv $WORKING_DIR/id_ed25519_github_deploy* $WORKING_DIR/archive/

ssh-keygen -t ed25519 -a 100 -f $WORKING_DIR/id_ed25519_github_deploy -q -N ""
ssh-keygen -s $WORKING_DIR/ca_key -I github -n ubuntu,ackersond -P "$CACERT_KEY_PASS" -V +10d -z $(date +%s) $WORKING_DIR/id_ed25519_github_deploy
CERT_INFO=`ssh-keygen -L -f $WORKING_DIR/id_ed25519_github_deploy-cert.pub`

pip install -r $WORKING_DIR/requirements.txt

# redeploys DigitalOcean infra with new keys and updates github secrets
if $WORKING_DIR/github_update_secrets.py ; then
    SLACK_URL=https://slack.com/api/chat.postMessage
    curl -s -d token=$SLACK_API_TOKEN -d channel=C092UE0H4 \
        -d text="$HOSTNAME just updated the SSH deploy key & cert in Org Secrets:" $SLACK_URL
    curl -s -d token=$SLACK_API_TOKEN -d channel=C092UE0H4 -d text="$CERT_INFO" $SLACK_URL
    source $GITHUB_DEPLOY_KEY_FILE
    ssh-copy-id -i $SSH_PRIV_KEY -o "IdentityFile $WORKING_DIR/archive/id_ed25519_github_deploy" -f vault
fi
