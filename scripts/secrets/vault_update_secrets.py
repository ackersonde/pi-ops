#!/usr/bin/env python3
from datetime import datetime
from types import SimpleNamespace

import github
import hvac
import os
import json
import re
import requests
import traceback
import vault


def main():
    read_token = vault.get_vault_token()

    if read_token:
        client = hvac.Client(url=vault.VAULT_API_ENDPOINT, token=read_token)
        if not client.is_authenticated():
            read_token = vault.get_vault_token()
            client = hvac.Client(url=vault.VAULT_API_ENDPOINT, token=read_token)

        vault_secrets = vault.get_updated_secrets_metadata(client)
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
    updates = {}

    # update the secrets which are out of sync on github
    for secret_name in vault_secrets.keys():
        vault_updated_at = re.sub(r"\..*?Z", "", vault_secrets[secret_name]) + "+00:00"
        vault_update_time = datetime.fromisoformat(vault_updated_at)

        if secret_name in github_secrets:
            github_updated_at = github_secrets[secret_name].replace("Z", "+00:00")
            github_update_time = datetime.fromisoformat(github_updated_at)

            # print(f'{secret_name} needs updating at Github: {github_update_time < vault_update_time}')

            if github_update_time < vault_update_time:
                secret = vault.get_secret_value(client, secret_name)
                for secret_name, value in secret.items():
                    json_args = SimpleNamespace(
                        name=secret_name, base64=True, value=value, filepath=""
                    )
                    github.update_secret(token_headers, github_public_key, json_args)
                    updates[
                        secret_name
                    ] = f"Updated github secret *{secret_name}* (changed in Vault on {vault_update_time})."

        else:
            secret = vault.get_secret_value(client, secret_name)
            for secret_name, value in secret.items():
                json_args = SimpleNamespace(
                    name=secret_name, base64=True, value=value, filepath=""
                )
                github.update_secret(token_headers, github_public_key, json_args)
                updates[
                    secret_name
                ] = f"Created *{secret_name}* @ github (added to Vault on {vault_update_time})."

    if len(updates) > 0:
        notify_slack(updates)


def notify_slack(updates):
    exception_method = "notify_slack():"
    impacted_repo_links = {}
    slack_update = ""

    try:
        for secret_name, update_text in updates.items():
            affected_repos = ""
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
                    " Following repos are affected and should be redeployed: "
                )

            if affected_repos != "":
                for _, link in impacted_repo_links.items():
                    affected_repos += link + ", "
                affected_repos = affected_repos.removesuffix(", ")

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
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
