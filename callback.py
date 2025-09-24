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
    
    project_url = os.environ.get("RAILWAY_STATIC_URL", "http://localhost:{}".format(port))
    callback_url = f"{project_url}/callback"
    
    print(f"Your callback URL is: {callback_url}")
    
    app.run(host="0.0.0.0", port=port)
