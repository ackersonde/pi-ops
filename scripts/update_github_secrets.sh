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

$WORKING_DIR/update_github_secrets.py
