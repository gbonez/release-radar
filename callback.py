from flask import Flask, request
import os

app = Flask(__name__)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    # Just log the code for now
    print("Received Spotify code:", code)
    return "Authorization complete! You can close this window."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway sets PORT env var
    app.run(host="0.0.0.0", port=port)
