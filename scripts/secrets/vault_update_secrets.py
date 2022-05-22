#!/usr/bin/env python3
from datetime import datetime
from types import SimpleNamespace

import github
import hvac
import os
import json
import re
import requests

VAULT_API_ENDPOINT = os.environ["VAULT_API_ENDPOINT"]
VAULT_READ_APPROLE_ID = os.environ["VAULT_READ_APPROLE_ID"]
VAULT_READ_SECRET_ID = os.environ["VAULT_READ_SECRET_ID"]
VAULT_WRITE_APPROLE_ID = os.environ["VAULT_WRITE_APPROLE_ID"]
VAULT_WRITE_SECRET_ID = os.environ["VAULT_WRITE_SECRET_ID"]


# https://hvac.readthedocs.io/en/stable/usage/auth_methods/approle.html
def get_vault_token(readonly=True) -> str:
    exception_method = "get_vault_token(): "
    vault_secret = VAULT_READ_SECRET_ID
    vault_role = VAULT_READ_APPROLE_ID
    token = ""
    if not readonly:
        vault_role = VAULT_WRITE_APPROLE_ID
        vault_secret = VAULT_WRITE_SECRET_ID

    try:
        client = hvac.Client(url=VAULT_API_ENDPOINT)
        r = client.auth.approle.login(
            role_id=vault_role,
            secret_id=vault_secret,
        )
        token = r["auth"]["client_token"]
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f"HTTP error occurred: {http_err}")  # Python 3.6
    except Exception as err:
        print(exception_method + f"Other error occurred: {err}")  # Python 3.6

    return token


def get_updated_secrets_metadata(client):
    exception_method = "get_updated_secrets_metadata(): "
    vault_secrets = {}

    try:
        # https://hvac.readthedocs.io/en/stable/usage/secrets_engines/kv_v2.html#read-secret-metadata
        # First LIST all secrets at secret engine "github/ackersonde"
        r = client.secrets.kv.v2.list_secrets(path="", mount_point="github/ackersonde")
        secret_names = r["data"]["keys"]

        # Second: LOOP thru each secret get last timestamp
        for secret_name in secret_names:
            r = client.secrets.kv.v2.read_secret_metadata(
                mount_point="github/ackersonde", path=secret_name
            )
            vault_secrets[secret_name] = r["data"]["updated_time"]
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f"HTTP error occurred: {http_err}")  # Python 3.6
    except Exception as err:
        print(exception_method + f"Other error occurred: {err}")  # Python 3.6

    return vault_secrets


def main():
    read_token = get_vault_token()

    if read_token:
        client = hvac.Client(url=VAULT_API_ENDPOINT, token=read_token)
        if not client.is_authenticated():
            read_token = get_vault_token()
            client = hvac.Client(url=VAULT_API_ENDPOINT, token=read_token)

        vault_secrets = get_updated_secrets_metadata(client)
        # print(vault_secrets)

        # print("=================================================================")

        # fetch the last updated time of the secrets on github
        github_secrets = github.get_updated_secrets_metadata()
        # print(len(github_secrets))

        update_github_secrets(vault_secrets, github_secrets, client)
    else:
        print(
            "Unable to get Vault token - cowardly refusing to fetch updated secrets..."
        )


def update_github_secrets(vault_secrets, github_secrets, client):
    token_headers = github.fetch_token_headers()
    github_public_key = github.fetch_public_key(token_headers)
    updates = []

    # update the secrets which are out of sync on github
    for secret_name in vault_secrets.keys():
        slack_update = ""
        vault_updated_at = re.sub(r"\..*?Z", "", vault_secrets[secret_name]) + "+00:00"
        vault_update_time = datetime.fromisoformat(vault_updated_at)

        if secret_name in github_secrets:
            github_updated_at = github_secrets[secret_name].replace("Z", "+00:00")
            github_update_time = datetime.fromisoformat(github_updated_at)

            # print(f'{secret_name} needs updating at Github: {github_update_time < vault_update_time}')

            if github_update_time < vault_update_time:
                secret = get_secret_value(client, secret_name)
                for secret_name, value in secret.items():
                    json_args = SimpleNamespace(
                        name=secret_name, base64=True, value=value, filepath=""
                    )
                    github.update_secret(token_headers, github_public_key, json_args)
                    slack_update = f"Updated github secret *{secret_name}* (changed in Vault on {vault_update_time})."
        else:
            secret = get_secret_value(client, secret_name)
            for secret_name, value in secret.items():
                json_args = SimpleNamespace(
                    name=secret_name, base64=True, value=value, filepath=""
                )
                github.update_secret(token_headers, github_public_key, json_args)
                slack_update = f"Created *{secret_name}* @ github (added to Vault on {vault_update_time})."

        if len(slack_update) > 0:
            updates[secret_name] = slack_update

    if len(updates) > 0:
        notify_slack(updates)


def notify_slack(updates):
    exception_method = "update_slack():"
    impacted_repo_links = {}
    affected_repos = ""

    slack_update = ""

    try:
        for secret_name, update_text in updates:
            headers = {}
            url = f"https://api.github.com/search/code?q=org%3Aackersonde+{secret_name}&type=Code"
            headers["Accept"] = "application/vnd.github.v3+json"
            r = requests.get(url, headers=headers)
            r.raise_for_status()

            j = r.json()
            for repository in j["items"]:
                impacted_repo_links[
                    repository["repository"]["name"]
                ] = f"<{repository['repository']['html_url']}|{repository['repository']['name']}>"
                affected_repos = (
                    " Following repos are effected and should be redeployed: "
                )

            for _, value in impacted_repo_links.items():
                affected_repos += value + ", "

            slack_update += update_text + affected_repos + "\n"

        if len(slack_update) > 0:
            r = requests.post(
                "https://slack.com/api/chat.postMessage",
                {
                    "token": os.environ["SLACK_API_TOKEN"],
                    "channel": "C092UE0H4",
                    "text": slack_update,
                },
            )
            r.raise_for_status()
    except json.decoder.JSONDecodeError as json_err:
        print(exception_method + f"JSON parsing error occurred: {json_err}")
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(exception_method + f"Other error occurred: {err}")


def get_secret_value(client, secret_name):
    exception_method = "get_secret_value(): "
    response = {}

    try:
        # https://hvac.readthedocs.io/en/stable/usage/secrets_engines/kv_v2.html#read-secret-versions
        r = client.secrets.kv.v2.read_secret_version(
            mount_point="github/ackersonde",
            path=secret_name,
        )
        response[secret_name] = r["data"]["data"][secret_name]
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f"HTTP error occurred: {http_err}")  # Python 3.6
    except Exception as err:
        print(exception_method + f"Other error occurred: {err}")  # Python 3.6

    return response


if __name__ == "__main__":
    main()
