
# %%
import requests
from presentation import present
from credential_offer import get_offer
from discover_capabilities import discover_capabilities
from authorize import authorize
from token_handler import get_token
from vc import get_vc

requests.packages.urllib3.disable_warnings()  # Disable SSL warnings


# %%
# get credentials
offer_uuid = get_offer()
discover_capabilities()
code = authorize(offer_uuid)
token = get_token(code)
vc = get_vc(token["access_token"])


# %%
# verify credentials
present(vc)
