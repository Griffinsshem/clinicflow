"""
Who is this request really from? The answer every rate limit is keyed on.

The problem
-----------
Browsers never call this API directly. Every request comes through the
Next.js server on Vercel, so the address Flask sees (after ProxyFix) is
one of Vercel's shared outbound IPs, not the visitor's. Keying limits on
that address merges every visitor into a handful of buckets: "3 demos per
hour per IP" quietly becomes "3 demos per hour for everyone", and one
person can exhaust the login limit for all users.

The fix
-------
The Next.js server forwards the visitor's address in X-Client-IP, along
with a shared secret in X-Proxy-Secret. The secret is what makes the
header trustworthy: this API is publicly reachable, so anyone can send
an X-Client-IP header, but only our own frontend knows the secret. A
caller without it gets keyed on their connecting address, exactly as
before, and cannot pick their own bucket by forging the header.
"""

import hmac
import ipaddress

from flask import current_app, request
from flask_limiter.util import get_remote_address

CLIENT_IP_HEADER = "X-Client-IP"
PROXY_SECRET_HEADER = "X-Proxy-Secret"


def _has_valid_proxy_secret() -> bool:
    expected = current_app.config.get("PROXY_SHARED_SECRET") or ""
    supplied = request.headers.get(PROXY_SECRET_HEADER, "")
    if not expected or not supplied:
        return False
    # Constant-time comparison, on bytes so non-ASCII input cannot raise.
    return hmac.compare_digest(supplied.encode(), expected.encode())


def client_ip() -> str:
    """
    The visitor's IP address, for rate limiting.

    Trusts X-Client-IP only when the request also carries the correct
    proxy secret and the header holds a well-formed IP address. Anything
    else falls back to the connecting address.
    """
    if _has_valid_proxy_secret():
        forwarded = request.headers.get(CLIENT_IP_HEADER, "").strip()
        try:
            return str(ipaddress.ip_address(forwarded))
        except ValueError:
            pass

    return get_remote_address()


def login_email_key() -> str:
    """
    Rate-limit key for login attempts against one account.

    The per-IP limit stops one machine hammering the endpoint; this stops
    many machines (a botnet, or anyone rotating IPs) guessing the password
    of one account. The email is normalised the same way authentication
    normalises it, so case and whitespace variations share one bucket.
    """
    payload = request.get_json(silent=True)
    email = payload.get("email") if isinstance(payload, dict) else None
    if isinstance(email, str) and email.strip():
        return f"login-email:{email.strip().lower()}"

    # No usable email: the request will fail validation anyway, so fall
    # back to the per-client bucket rather than one shared "no email" key.
    return f"login-email-missing:{client_ip()}"
