from flask import Flask, request
import os
import json
import requests

app = Flask(__name__)

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = (os.environ.get("BASE_URL") or "http://localhost:5000") + "/callback"
TOKENS_FILE = "tokens.json"

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "No code provided!", 400

    print("🎧 Received Spotify authorization code:", code)

    # Exchange the code for an access + refresh token
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        print("❌ Failed to get tokens:", response.text)
        return "Error exchanging code for tokens. Check logs."

    tokens = response.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    print("✅ Access token:", access_token)
    print("🔁 Refresh token:", refresh_token)

    # Save tokens to file
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
        print(f"💾 Tokens saved to {TOKENS_FILE}")

    return "Authorization complete! You can close this window."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    project_url = os.environ.get("RAILWAY_STATIC_URL", f"http://localhost:{port}")
    callback_url = f"{project_url}/callback"

    print(f"🚀 Your callback URL is: {callback_url}")
    print("Once you authorize, check Railway logs for your refresh token!")

    app.run(host="0.0.0.0", port=port)
