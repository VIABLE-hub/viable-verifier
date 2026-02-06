from cfg import host
from utils import pp_json
import requests


def openid_credential_issuer():
    response = requests.get(
        f"{host}.well-known/openid-credential-issuer",
        allow_redirects=True,
        verify=False,
    )
    openid_credential_issuer_res = response.json()
    # pp_json(openid_credential_issuer_res)
    return openid_credential_issuer_res


def oauth_authorization_server():
    response = requests.get(
        f"{host}.well-known/oauth-authorization-server",
        allow_redirects=True,
        verify=False,
    )
    oauth_authorization_server_res = response.json()
    # pp_json(oauth_authorization_server_res)
    return oauth_authorization_server_res


def openid_configuration():
    response = requests.get(
        f"{host}.well-known/openid-configuration",
        allow_redirects=True,
        verify=False,
    )
    openid_configuration_res = response.json()
    # pp_json(openid_configuration_res)
    return openid_configuration_res


def discover_capabilities():
    # TODO: their issuer probably replaces "openid-configuration" with "oauth-authorization-server"
    openid_credential_issuer()
    openid_configuration()
