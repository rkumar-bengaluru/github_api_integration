import time
import jwt
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv         # helps read secret keys from .env file
import os 



# 1. Load secret keys from .env file (never write keys directly in code!)
load_dotenv()


SYMPHONY_GITHUB_APP_ID    = os.getenv("SYMPHONY_GITHUB_APP_ID")         # your OpenAI key
SYMPHONY_GITHUB_CLIENT_ID        = os.getenv("SYMPHONY_GITHUB_CLIENT_ID")            # example: https://xxxxxx.us-east.aws.cloud.qdrant.io
SYMPHONY_GITHIB_INSTALLATION_ID    = os.getenv("SYMPHONY_GITHIB_INSTALLATION_ID")         # your Qdrant cloud key

# Check if we have all keys
if not all([SYMPHONY_GITHUB_APP_ID, SYMPHONY_GITHUB_CLIENT_ID, SYMPHONY_GITHIB_INSTALLATION_ID]):
    print("Error! Missing some secret keys in .env file.")
    print("Need: SYMPHONY_GITHUB_APP_ID, SYMPHONY_GITHUB_CLIENT_ID, SYMPHONY_GITHIB_INSTALLATION_ID")
    exit()

PRIVATE_KEY = open(".\keys\symphony-agent.2026-02-27.private-key.pem", "rb").read()
BASE_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# Cache
_install_token = None
_install_expires_at = 0  # unix timestamp

def get_installation_token():
    global _install_token, _install_expires_at

    now = time.time()
    if _install_token and now < _install_expires_at - 300:  # 5 min buffer
        return _install_token

    # Generate fresh JWT
    payload = {
        "iat": int(now) - 60,
        "exp": int(now) + 600,  # 10 min
        "iss": SYMPHONY_GITHUB_APP_ID
    }
    jwt_token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

    # Get new installation token
    url = f"https://api.github.com/app/installations/{SYMPHONY_GITHIB_INSTALLATION_ID}/access_tokens"
    resp = requests.post(url, headers={**BASE_HEADERS, "Authorization": f"Bearer {jwt_token}"})
    resp.raise_for_status()

    data = resp.json()
    _install_token = data["token"]
    expires_at_str = data["expires_at"]  # ISO string
    dt = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
    _install_expires_at = dt.timestamp()

    print(f"New token expires at {expires_at_str}")
    return _install_token

# Example: List open PRs
def list_open_prs(owner, repo):
    token = get_installation_token()
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=open"
    resp = requests.get(url, headers={**BASE_HEADERS, "Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    print(resp.json())
    return resp.json()

# Usage
prs = list_open_prs("rkumar-bengaluru", "SymphonyBackend")
for pr in prs:
    print(f"#{pr['number']} - {pr['title']}")