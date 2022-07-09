#!/usr/bin/env python3
from pathlib import Path
from types import SimpleNamespace

import base64
import hvac
import os
import requests
import traceback

mount_point = "github/ackersonde"

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
        print(exception_method + f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(exception_method + f"Other error occurred: {err}")
        print(traceback.format_exc())

    return token


def update_secret(args: SimpleNamespace):
    secret_name = args.name
    if secret_name.startswith("CTX_"):
        secret_name = secret_name.replace("CTX_", "ORG_")
    if secret_name.endswith("_B64"):
        secret_name = secret_name.removesuffix("_B64")

    # b64encode = args.base64 # not doing this in Vault
    b64encode = False

    payload = ""
    if args.filepath:
        file = Path(args.filepath)
        if b64encode:
            base64_bytes = base64.b64encode(file.read_bytes())
            payload = base64_bytes.decode("utf-8")
        else:
            payload = file.read_text()
    else:
        payload = args.value
        if b64encode:
            base64_bytes = base64.b64encode(bytes(payload, "utf-8"))
            payload = base64_bytes.decode("utf-8")

    write_secret(secret_name, payload)


def write_secret(secret_name, secret_value):
    exception_method = "write_secret(): "
    write_token = get_vault_token(readonly=False)

    try:
        client = hvac.Client(url=VAULT_API_ENDPOINT, token=write_token)
        secret = {}
        secret[secret_name] = secret_value
        client.secrets.kv.v2.create_or_update_secret(
            mount_point=mount_point,
            path=secret_name,
            secret=secret,
        )
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(exception_method + f"Other error occurred: {err}")
        print(traceback.format_exc())


def get_updated_secrets_metadata(client):
    exception_method = "get_updated_secrets_metadata(): "
    vault_secrets = {}

    try:
        # https://hvac.readthedocs.io/en/stable/usage/secrets_engines/kv_v2.html#read-secret-metadata
        # First LIST all secrets at secret engine "github/ackersonde"
        r = client.secrets.kv.v2.list_secrets(mount_point=mount_point, path="")
        secret_names = r["data"]["keys"]

        # Second: LOOP thru each secret get last timestamp
        for secret_name in secret_names:
            r = client.secrets.kv.v2.read_secret_metadata(
                mount_point=mount_point,
                path=secret_name,
            )
            vault_secrets[secret_name] = r["data"]["updated_time"]
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(exception_method + f"Other error occurred: {err}")
        print(traceback.format_exc())

    return vault_secrets


def get_secret_value(client, secret_name):
    exception_method = "get_secret_value(): "
    response = {}

    try:
        # https://hvac.readthedocs.io/en/stable/usage/secrets_engines/kv_v2.html#read-secret-versions
        r = client.secrets.kv.v2.read_secret_version(
            mount_point=mount_point,
            path=secret_name,
        )
        response[secret_name] = r["data"]["data"][secret_name]
    except requests.exceptions.HTTPError as http_err:
        print(exception_method + f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(exception_method + f"Other error occurred: {err}")
        print(traceback.format_exc())

    return response
