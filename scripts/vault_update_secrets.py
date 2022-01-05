import github
import os
import json
import requests

BASICAUTH_USER = os.environ['BASICAUTH_USER']
BASICAUTH_PASS = os.environ['BASICAUTH_PASS']
VAULT_USER = os.environ['VAULT_USER']
VAULT_PASS = os.environ['VAULT_PASS']
VAULT_API_ENDPOINT = os.environ['VAULT_API_ENDPOINT']
VAULT_TOKEN = os.environ['VAULT_TOKEN']


def get_vault_token(auth, headers):
    exception_method = "getVaultToken(): "

    try:
        url = VAULT_API_ENDPOINT + '/v1/auth/userpass/login/' + VAULT_USER
        data = '{"password": "' + VAULT_PASS + '", "ttl": "1h" }'

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

def get_updated_secrets(auth, headers, token, vault_secrets):
    exception_method = "getUpdatedSecrets(): "

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
          vault_secrets.append({secret_name: j['data']['updated_time']})
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

    token = VAULT_TOKEN
    if token == "":
      token = get_vault_token(auth, headers)
      print(token)

    if token:
      vault_secrets = []
      vault_secrets = get_updated_secrets(auth, headers, token, vault_secrets)
      print(vault_secrets)

      # fetch the last updated time of the secrets on github
      github_secrets = github.get_updated_secrets_metadata()
      print(github_secrets)

      # TODO: update the secrets which are out of sync on github
      # for vault_secret in vault_secrets.keys():
      #   if github_secrets[vault_secret]:
      #     if github_secrets[vault_secret] < vault_secrets[vault_secret]:
      #       update_github_secret(vault_secret)
      #     else:
      #       # NO OP as secret hasn't changed
      #   else:
      #     create_github_secret(vault_secret) # as this secret isn't known to github
    else:
      print("Unable to get Vault token - cowardly refusing to fetch updated secrets...")

if __name__ == '__main__':
    main()
