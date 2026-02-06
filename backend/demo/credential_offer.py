from cfg import host, holder_did
from utils import pp_json
import requests


def get_credentual_offer_uri():
    # try read qr code from clipboard
    offer_res = try_url_from_clipboard()
    if not offer_res:
        response = requests.post(
            f"{host}offer",
            allow_redirects=False,
            verify=False,
        )
        offer_res = response.headers["location"]

    credentual_offer_uri = offer_res[offer_res.rfind(
        'openid-credential-offer://?credential_offer_uri=')+47:]
    print(credentual_offer_uri)
    cutoff = credentual_offer_uri.rfind('/')
    uuid = credentual_offer_uri[cutoff+1:]
    return credentual_offer_uri, uuid


def try_url_from_clipboard():
    try:
        from PIL import Image, ImageGrab
        from pyzbar.pyzbar import decode
        img = ImageGrab.grabclipboard()
        data = decode(img)
        data = data[0].data.decode("utf-8")
        return data
    except Exception as e:
        print(f"error: {e}")
        return None


def get_offer():
    offer, uuid = get_credentual_offer_uri()
    return uuid
