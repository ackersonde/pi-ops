from datetime import datetime
from types import SimpleNamespace

import github
import os
import json
import re
import requests

BASICAUTH_USER = os.environ['BASICAUTH_USER']
BASICAUTH_PASS = os.environ['BASICAUTH_PASS']
VAULT_API_ENDPOINT = os.environ['VAULT_API_ENDPOINT']
VAULT_READ_USER = os.environ['VAULT_READ_USER']
VAULT_READ_PASS = os.environ['VAULT_READ_PASS']
VAULT_READ_TOKEN = os.environ['VAULT_READ_TOKEN']
VAULT_WRITE_USER = os.environ['VAULT_WRITE_USER']
VAULT_WRITE_PASS = os.environ['VAULT_WRITE_PASS']
VAULT_WRITE_TOKEN = os.environ['VAULT_WRITE_TOKEN']


def get_vault_token(auth, headers, readonly=True):
    exception_method = "get_vault_token(): "
    vault_user = VAULT_READ_USER
    vault_pass = VAULT_READ_PASS

    if not readonly:
        vault_user = VAULT_WRITE_USER
        vault_pass = VAULT_WRITE_PASS

    try:
        url = VAULT_API_ENDPOINT + '/v1/auth/userpass/login/' + vault_user
        data = '{"password": "' + vault_pass + '", "ttl": "1h" }'

        r = requests.post(url, auth=auth, headers=headers, data=data)
        r.raise_for_status()

        j = r.json()
        token = j['auth']['client_token']
    except json.decoder.JSONDecodeError as json_err:
        print(exception_method + f'JSON parsing error occurred: {json_err}')
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
        print(exception_method + f'Other error occurred: {err}')  # Python 3.6

    return token


def get_updated_secrets_metadata(auth, headers, token):
    exception_method = "get_updated_secrets(): "
    vault_secrets = {}

    try:
        # First LIST all secrets at secret engine "github/ackersonde"
        url = VAULT_API_ENDPOINT + "/v1/github%2Fackersonde/metadata/?list=1"
        headers["X-Vault-Token"] = token

        r = requests.get(url, auth=auth, headers=headers)
        r.raise_for_status()

        j = r.json()
        secret_names = j['data']['keys']

        # Second: LOOP thru each secret get last timestamp
        for secret_name in secret_names:
          url = VAULT_API_ENDPOINT + "/v1/github%2Fackersonde/metadata/" + secret_name

          r = requests.get(url, auth=auth, headers=headers)
          r.raise_for_status()

          j = r.json()
          vault_secrets[secret_name] = j['data']['updated_time']
    except json.decoder.JSONDecodeError as json_err:
        print(exception_method + f'JSON parsing error occurred: {json_err}')
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
        print(exception_method + f'Other error occurred: {err}')  # Python 3.6

    return vault_secrets


def main():
    auth = requests.auth.HTTPBasicAuth(BASICAUTH_USER, BASICAUTH_PASS)

    headers = requests.structures.CaseInsensitiveDict()
    headers["Content-Type"] = "application/json"

    read_token = VAULT_READ_TOKEN
    if read_token == "":
        read_token = get_vault_token(auth, headers, readonly = True)
        print(f'READ: {read_token}')

    if read_token:
        vault_secrets = get_updated_secrets_metadata(auth, headers, read_token)
        # print(vault_secrets)

        # print('=================================================================')

        # fetch the last updated time of the secrets on github
        github_secrets = github.get_updated_secrets_metadata()
        # print(len(github_secrets))

        update_github_secrets(vault_secrets, github_secrets, auth, headers, read_token)
    else:
        print("Unable to get Vault token - cowardly refusing to fetch updated secrets...")


def update_github_secrets(vault_secrets, github_secrets, auth, headers, read_token):
    token_headers = github.fetch_token_headers()
    github_public_key = github.fetch_public_key(token_headers)

    # update the secrets which are out of sync on github
    for secret_name in vault_secrets.keys():
        slack_update = ""

        if secret_name in github_secrets:
            github_updated_at = github_secrets[secret_name].replace("Z", "+00:00")
            github_update_time = datetime.fromisoformat(github_updated_at)

            vault_updated_at = re.sub("\..*?Z", "", vault_secrets[secret_name]) + "+00:00"
            vault_update_time = datetime.fromisoformat(vault_updated_at)

            #print(f'{secret_name} needs updating at Github: {github_update_time < vault_update_time}')

            if github_update_time < vault_update_time:
                secret = get_secret_value(auth, headers, read_token, secret_name)
                for secret_name, value in secret.items():
                    json_args = SimpleNamespace(name=secret_name, base64=True, value=value, filepath='')
                    github.update_secret(token_headers, github_public_key, json_args)
                    slack_update = f'Updated github w/ *{secret_name}*.'
        else:
            secret = get_secret_value(auth, headers, read_token, secret_name)
            for secret_name, value in secret.items():
                json_args = SimpleNamespace(name=secret_name, base64=True, value=value, filepath='')
                github.update_secret(token_headers, github_public_key, json_args)
                slack_update = f'Created *{secret_name}* @ github.'

        if slack_update:
            update_slack(slack_update, secret_name)


def update_slack(slack_update, secret_name):
    exception_method = "update_slack():"
    impacted_repo_links = ""

    try:
        headers = {}
        url = f'https://api.github.com/search/code?q=org%3Aackersonde+{secret_name}&type=Code'
        headers['Accept'] = "application/vnd.github.v3+json"
        r = requests.get(url, headers=headers)
        r.raise_for_status()

        j = r.json()
        for repository in j['items']:
            impacted_repo_links += f"<{repository['repository']['html_url']} | {repository['repository']['name']}>, "

        if impacted_repo_links:
            impacted_repo_links = " Following repos are effected and should be redeployed: " + impacted_repo_links.removesuffix(", ")
            slack_update += impacted_repo_links

        print(slack_update)
        r = requests.post('https://slack.com/api/chat.postMessage', {
            'token': os.environ['SLACK_API_TOKEN'],
            'channel': 'C092UE0H4',
            'text': slack_update
            })
        r.raise_for_status()
    except json.decoder.JSONDecodeError as json_err:
        print(exception_method + f'JSON parsing error occurred: {json_err}')
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
        print(exception_method + f'Other error occurred: {err}')  # Python 3.6


def get_secret_value(auth, headers, token, secret_name):
    exception_method = "get_secret_value(): "
    response = {}

    try:
        headers["X-Vault-Token"] = token
        url = VAULT_API_ENDPOINT + "/v1/github%2Fackersonde/data/" + secret_name
        r = requests.get(url, auth=auth, headers=headers)
        r.raise_for_status()
        j = r.json()
        response[secret_name] = j['data']['data'][secret_name]
    except json.decoder.JSONDecodeError as json_err:
        print(exception_method + f'JSON parsing error occurred: {json_err}')
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
        print(exception_method + f'Other error occurred: {err}')  # Python 3.6

    return response


if __name__ == '__main__':
    main()
