#!/usr/bin/env python3
from requests.exceptions import HTTPError
from types import SimpleNamespace

import os
import requests

import github

SSH_CERT_FILE = os.environ['SSH_CERT_FILE']
SSH_PRIV_KEY = os.environ['SSH_PRIV_KEY']
SSH_PUB_KEY = os.environ['SSH_PUB_KEY']
ACME_JSON = "/home/ubuntu/traefik/acme.json"


def redeploy_digitalocean(token_headers: str):
    resp = requests.post(
        'https://api.github.com/repos/ackersonde/digitaloceans/actions/workflows/build.yml/dispatches',
        json={"ref": "main"},
        headers=token_headers)
    resp.raise_for_status()


def main():
    # https://docs.github.com/en/free-pro-team@latest/rest/reference/actions#secrets
    try:
        token_headers = github.fetch_token_headers()
        github_public_key = github.fetch_public_key(token_headers)

        ssh_priv_key_args = SimpleNamespace(
            name='CTX_SERVER_DEPLOY_SECRET_B64', base64=True, filepath=SSH_PRIV_KEY)
        github.update_secret(token_headers, github_public_key, ssh_priv_key_args)

        ssh_cert_file_args = SimpleNamespace(
            name='CTX_SERVER_DEPLOY_CACERT_B64', base64=True, filepath=SSH_CERT_FILE)
        github.update_secret(token_headers, github_public_key, ssh_cert_file_args)

        ssh_pub_key_args = SimpleNamespace(
            name='CTX_SERVER_DEPLOY_PUBLIC_B64', base64=True, filepath=SSH_PUB_KEY)
        github.update_secret(token_headers, github_public_key, ssh_pub_key_args)

        acme_json_args = SimpleNamespace(
            name='CTX_ACME_JSON', base64=False, filepath=ACME_JSON)
        github.update_secret(token_headers, github_public_key, acme_json_args)

        redeploy_digitalocean(token_headers)
    except HTTPError as http_err:
        github.fatal(f'HTTP error occurred: {http_err}')
    except Exception as err:
        github.fatal(f'Other error occurred: {err}')


if __name__ == '__main__':
    main()
