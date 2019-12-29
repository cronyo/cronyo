import sys
sys.path.insert(0, './vendor')
try:
    from cronyo.config import config
    from cronyo import logger
except ImportError:
    from config import config
    import logger

import time
import hashlib
import hmac
import requests

logger = logger.setup()

# the sign method takes a message and a secret key, and returns a
# hex-based hmac signature (using sha256), as well as a time-based nonce
def sign(message, secret_key):
    t = int(time.time())
    return t, hmac.new(
        secret_key.encode("utf8"),
        "{}.{}".format(t, message).encode("utf8"),
        hashlib.sha256
    ).hexdigest()

# this is the main lambda handler, it gets triggered with an event
# the event is set on Cloudwatch
def http_post(event, _context):
    logger.info(event)
    url = event["url"]
    headers = event.get("headers", {"User-Agent": "Cronyo"})
    cookies = event.get("cookies", {})
    params = event.get("params", {})
    data = event.get("data", {})
    # secret_key is defined in our config
    secret_key = config["secret_key"]
    # our signature protects the whole url
    t, signature = sign(url, secret_key)
    signature_header = {"X-Signature": "t={},signature={}".format(t, signature)}
    logger.info("t={},signature={}".format(t, signature))
    headers.update(signature_header)
    data.update({"signature": signature, "t": t}),
    # POSTing a request to the url, and passing the signature and the nonce as header as well as params
    r = requests.post(
        url,
        data=data,
        headers=headers,
        params=params,
        cookies=cookies
    )
    logger.info(
        "response status: {} body: {} headers: {}".format(
            r.status_code, r.text, r.headers
        )
    )
    return r.status_code

def http_get(event, _context):
    logger.info(event)
    url = event["url"]
    headers = event.get("headers", {"User-Agent": "Cronyo"})
    cookies = event.get("cookies", {})
    params = event.get("params", {})
    # secret_key is defined in our config
    secret_key = config["secret_key"]
    # our signature protects the whole url
    t, signature = sign(url, secret_key)
    signature_header = {"X-Signature": "t={},signature={}".format(t, signature)}
    logger.info("t={},signature={}".format(t, signature))
    headers.update(signature_header)
    # GETing a request to the url, and passing the signature and the nonce only as header
    r = requests.get(
        url,
        headers=headers,
        params=params,
        cookies=cookies
    )
    logger.info(
        "response status: {} body: {} headers: {}".format(
            r.status_code, r.text, r.headers
        )
    )
    return r.status_code
