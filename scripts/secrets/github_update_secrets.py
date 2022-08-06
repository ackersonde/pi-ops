#!/usr/bin/env python3
from requests.exceptions import HTTPError
from types import SimpleNamespace

import os
import requests

import github
import vault

SSH_CERT_FILE = os.environ["SSH_CERT_FILE"]
SSH_PRIV_KEY = os.environ["SSH_PRIV_KEY"]
SSH_PUB_KEY = os.environ["SSH_PUB_KEY"]
TLS_ACKDE_CRT = "/etc/letsencrypt/live/ackerson.de/fullchain.pem"
TLS_ACKDE_KEY = "/etc/letsencrypt/live/ackerson.de/privkey.pem"
TLS_HAUSM_CRT = "/etc/letsencrypt/live/hausmeisterservice-planb.de/fullchain.pem"
TLS_HAUSM_KEY = "/etc/letsencrypt/live/hausmeisterservice-planb.de/privkey.pem"


def redeploy_hetzner(token_headers: str):
    resp = requests.post(
        "https://api.github.com/repos/ackersonde/hetzner_home/actions/workflows/build.yml/dispatches",
        json={"ref": "main"},
        headers=token_headers,
    )
    resp.raise_for_status()


def main():
    # https://docs.github.com/en/free-pro-team@latest/rest/reference/actions#secrets
    try:
        token_headers = github.fetch_token_headers()
        github_public_key = github.fetch_public_key(token_headers)

        ssh_priv_key_args = SimpleNamespace(
            name="ORG_SERVER_DEPLOY_SECRET", base64=True, filepath=SSH_PRIV_KEY
        )
        github.update_secret(token_headers, github_public_key, ssh_priv_key_args)
        vault.update_secret(ssh_priv_key_args)

        ssh_cert_file_args = SimpleNamespace(
            name="ORG_SERVER_DEPLOY_CACERT", base64=True, filepath=SSH_CERT_FILE
        )
        github.update_secret(token_headers, github_public_key, ssh_cert_file_args)
        vault.update_secret(ssh_cert_file_args)

        ssh_pub_key_args = SimpleNamespace(
            name="ORG_SERVER_DEPLOY_PUBLIC", base64=True, filepath=SSH_PUB_KEY
        )
        github.update_secret(token_headers, github_public_key, ssh_pub_key_args)
        vault.update_secret(ssh_pub_key_args)

        ackde_crt_args = SimpleNamespace(
            name="ORG_TLS_ACKDE_CRT", base64=True, filepath=TLS_ACKDE_CRT
        )
        github.update_secret(token_headers, github_public_key, ackde_crt_args)
        vault.update_secret(ackde_crt_args)

        ackde_key_args = SimpleNamespace(
            name="ORG_TLS_ACKDE_KEY", base64=True, filepath=TLS_ACKDE_KEY
        )
        github.update_secret(token_headers, github_public_key, ackde_key_args)
        vault.update_secret(ackde_key_args)

        hausm_crt_args = SimpleNamespace(
            name="ORG_TLS_HAUSM_CRT", base64=True, filepath=TLS_HAUSM_CRT
        )
        github.update_secret(token_headers, github_public_key, hausm_crt_args)
        vault.update_secret(hausm_crt_args)

        hausm_key_args = SimpleNamespace(
            name="ORG_TLS_HAUSM_KEY", base64=True, filepath=TLS_HAUSM_KEY
        )
        github.update_secret(token_headers, github_public_key, hausm_key_args)
        vault.update_secret(hausm_key_args)

        redeploy_hetzner(token_headers)
    except HTTPError as http_err:
        github.fatal(f"HTTP error occurred: {http_err}")
    except Exception as err:
        github.fatal(f"Other error occurred: {err}")


if __name__ == "__main__":
    main()
