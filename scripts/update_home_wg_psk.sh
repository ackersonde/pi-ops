#!/bin/bash
WORKING_DIR=/home/ubuntu/my-ca
VAULT_UPDATE_GITHUB_FILE=~/.ssh/vault_update_github_params
if [ -s "$VAULT_UPDATE_GITHUB_FILE" ]; then
    source $VAULT_UPDATE_GITHUB_FILE
else
    echo "$VAULT_UPDATE_GITHUB_FILE required. No params == no run."
    exit
fi
GITHUB_DEPLOY_KEY_FILE=~/.ssh/github_deploy_params
if [ -s "$GITHUB_DEPLOY_KEY_FILE" ]; then
    source $GITHUB_DEPLOY_KEY_FILE
else
    echo "$GITHUB_DEPLOY_KEY_FILE required. No params == no run."
    exit
fi
export GITHUB_SECRETS_PK_PEM=$(cat $GITHUB_SECRETS_PK_PEM_FILE)

# Generate new PresharedKey & Restart Wireguard
ssh -o StrictHostKeyChecking=no homepage 'sed -it "s|.*PresharedKey.*|PresharedKey = $(wg genpsk)|" /etc/wireguard/wg.conf'
ssh homepage 'wg-quick down wg; wg-quick up wg' # restart wireguard w/ new key

# Save and share new PSK
export NEW_PSK=$(ssh homepage cat /etc/wireguard/wg.conf | grep PresharedKey | awk '{print $3}')
$WORKING_DIR/vault.py ORG_WG_DO_HOME_PRESHAREDKEY $NEW_PSK

# the *data-urlencode* keeps the %2F from being translated into a '/' in Slack!
curl -s -o /dev/null -X POST -d "token=$SLACK_API_TOKEN" -d "channel=U092UC9EW" \
--data-urlencode "text=New PSK is <https://vault.ackerson.de/ui/vault/secrets/github%2Fackersonde/show/ORG_WG_DO_HOME_PRESHAREDKEY|now available>" \
https://slack.com/api/chat.postMessage
