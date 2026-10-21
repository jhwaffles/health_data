import json
import os
import secrets
import hashlib
import base64
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode
from threading import Event

import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(REPO_ROOT, "source_data")
OAUTH_PATH = os.path.join(SOURCE_DIR, "oura_oauth.json")

AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"
DEFAULT_REDIRECT_URI = "http://localhost:8000/callback"
DEFAULT_SCOPES = "daily personal heartrate workout tag session spo2"
EXPIRY_SKEW_SECONDS = 60

DEFAULT_OAUTH = {
    "client_id": "",
    "client_secret": "",
    "redirect_uri": DEFAULT_REDIRECT_URI,
    "scope": DEFAULT_SCOPES,
    "access_token": "",
    "refresh_token": "",
    "expires_at": 0,
}


def _pkce_pair():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def load_oauth():
    os.makedirs(SOURCE_DIR, exist_ok=True)
    if not os.path.exists(OAUTH_PATH):
        save_oauth(DEFAULT_OAUTH)
        return dict(DEFAULT_OAUTH)
    with open(OAUTH_PATH, "r") as f:
        data = json.load(f)
    merged = dict(DEFAULT_OAUTH)
    merged.update({k: v for k, v in data.items() if v is not None})
    return merged


def save_oauth(data):
    os.makedirs(SOURCE_DIR, exist_ok=True)
    with open(OAUTH_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    try:
        os.chmod(OAUTH_PATH, 0o600)
    except OSError:
        pass


def _has_credentials(oauth):
    return bool(oauth.get("client_id")) and bool(oauth.get("client_secret"))


def _token_is_fresh(oauth):
    token = oauth.get("access_token")
    expires_at = float(oauth.get("expires_at") or 0)
    if not token:
        return False
    if not expires_at:
        return True
    return time.time() < (expires_at - EXPIRY_SKEW_SECONDS)


def _store_token_response(oauth, payload):
    oauth["access_token"] = payload["access_token"]
    if payload.get("refresh_token"):
        oauth["refresh_token"] = payload["refresh_token"]
    expires_in = int(payload.get("expires_in") or 0)
    oauth["expires_at"] = int(time.time()) + expires_in if expires_in else 0
    save_oauth(oauth)
    return oauth["access_token"]


def _refresh_access_token(oauth):
    refresh_token = oauth.get("refresh_token")
    if not refresh_token:
        return None
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": oauth["client_id"],
            "client_secret": oauth["client_secret"],
        },
        timeout=30,
    )
    if response.status_code != 200:
        print(f"Token refresh failed ({response.status_code}): {response.text}")
        return None
    return _store_token_response(oauth, response.json())


def _wait_for_auth_code(redirect_uri):
    parsed = urlparse(redirect_uri)
    host = "127.0.0.1" if parsed.hostname in (None, "localhost") else parsed.hostname
    port = parsed.port or 80
    path = parsed.path or "/callback"
    result = {"code": None, "error": None}
    done = Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            request = urlparse(self.path)
            if request.path != path:
                self.send_response(404)
                self.end_headers()
                return
            params = parse_qs(request.query)
            result["code"] = (params.get("code") or [None])[0]
            result["error"] = (params.get("error") or [None])[0]
            body = b"Oura authorization complete. You can close this tab and return to the terminal."
            if result["error"] or not result["code"]:
                body = b"Oura authorization failed. Return to the terminal for details."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            done.set()

        def log_message(self, format, *args):
            return

    server = HTTPServer((host, port), Handler)
    try:
        while not done.wait(timeout=0.25):
            server.handle_request()
    finally:
        server.server_close()

    if result["error"]:
        raise RuntimeError(f"Oura authorization denied: {result['error']}")
    if not result["code"]:
        raise RuntimeError("Oura authorization did not return a code.")
    return result["code"]


def login(oauth=None):
    oauth = oauth or load_oauth()
    if not _has_credentials(oauth):
        save_oauth(oauth)
        raise RuntimeError(
            "Missing Oura client_id / client_secret.\n"
            f"1. Create an API application at https://cloud.ouraring.com\n"
            f"2. Set the redirect URI to {oauth.get('redirect_uri') or DEFAULT_REDIRECT_URI}\n"
            f"3. Put client_id and client_secret in {OAUTH_PATH}\n"
            "4. Re-run this script."
        )

    redirect_uri = oauth.get("redirect_uri") or DEFAULT_REDIRECT_URI
    oauth["redirect_uri"] = redirect_uri
    verifier, challenge = _pkce_pair()
    params = {
        "response_type": "code",
        "client_id": oauth["client_id"],
        "redirect_uri": redirect_uri,
        "state": secrets.token_urlsafe(16),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    # Omit scope so Oura requests every scope enabled on the API application.
    auth_url = f"{AUTHORIZE_URL}?{urlencode(params)}"
    print("Opening Oura authorization in your browser...")
    print(auth_url)
    webbrowser.open(auth_url)
    print(f"Waiting for redirect to {redirect_uri} ...")
    code = _wait_for_auth_code(redirect_uri)

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": oauth["client_id"],
            "client_secret": oauth["client_secret"],
            "code_verifier": verifier,
        },
        timeout=30,
    )
    response.raise_for_status()
    token = _store_token_response(oauth, response.json())
    print(f"Authorized. Tokens saved to {OAUTH_PATH}")
    return token


def get_access_token(force_login=False):
    oauth = load_oauth()
    if force_login:
        return login(oauth)
    if _token_is_fresh(oauth):
        return oauth["access_token"]
    refreshed = _refresh_access_token(oauth)
    if refreshed:
        print("Refreshed Oura access token.")
        return refreshed
    return login(oauth)


if __name__ == "__main__":
    get_access_token(force_login=True)
