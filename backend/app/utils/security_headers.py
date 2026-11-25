"""
Security headers on every API response.

The API only ever returns JSON, and much of it is patient data. These
headers make sure that data is never stored in a cache, never
interpreted as anything but JSON, and never rendered inside a page.

They are set on every response, errors and rate-limit refusals
included, because an error body can carry data too and because a
header that is only "usually" present protects nothing.
"""

from flask import Flask, Response

SECURITY_HEADERS = {
    # Patient data must not be kept by the browser, a proxy or a CDN.
    # A shared computer's back button or disk cache must not reveal it.
    "Cache-Control": "no-store",
    # A JSON body is never sniffed into HTML or script.
    "X-Content-Type-Options": "nosniff",
    # A JSON API has nothing to load and should never be framed. If a
    # response were ever opened as a page, nothing in it could run.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "X-Frame-Options": "DENY",
    # API URLs carry record IDs; never pass them on to another site.
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-site",
}


def _apply(response: Response) -> Response:
    for name, value in SECURITY_HEADERS.items():
        response.headers[name] = value
    return response


def register_security_headers(app: Flask) -> None:
    app.after_request(_apply)
