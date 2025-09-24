import os
import json
import datetime
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from twilio.rest import Client

# ==== CONFIGURATION ====
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.environ.get("BASE_URL") + "/callback"

TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.environ.get("TWILIO_PHONE")
MY_PHONE = os.environ.get("MY_PHONE")

ARTISTS_FILE = "artists.json"
RELEASES_FILE = "releases.json"

scope = "user-library-read playlist-modify-private playlist-modify-public"
sp = Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=scope
))

# ==== STEP 1: Load liked songs & track artists ====
def update_artists_file():
    if os.path.exists(ARTISTS_FILE):
        with open(ARTISTS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"last_track_id": None, "artists": {}}

    results = sp.current_user_saved_tracks(limit=50)
    items = results["items"]

    newest_track = items[0]["track"]
    newest_track_id = newest_track["id"]

    if data["last_track_id"] == newest_track_id:
        print("No new liked songs.")
        return data

    # Get artists from liked tracks until last saved
    for item in items:
        track = item["track"]
        track_id = track["id"]
        if track_id == data["last_track_id"]:
            break
        for artist in track["artists"]:
            data["artists"][artist["id"]] = artist["name"]

    data["last_track_id"] = newest_track_id

    with open(ARTISTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return data

# ==== STEP 2: Check new releases per artist ====
def check_new_releases(artists_data):
    releases = []

    for artist_id, artist_name in artists_data["artists"].items():
        albums = sp.artist_albums(artist_id, album_type="album,single", limit=5)
        for album in albums["items"]:
            release_date = album["release_date"]
            release_type = album["album_type"]  # single or album
            track_count = album["total_tracks"]

            # Heuristic classification
            if track_count <= 3:
                r_type = "single"
            elif track_count <= 6:
                r_type = "ep"
            else:
                r_type = "album"

            # Check release is recent (within 1 day)
            release_dt = datetime.datetime.strptime(release_date, "%Y-%m-%d")
            if (datetime.datetime.now() - release_dt).days <= 1:
                releases.append({
                    "name": album["name"],
                    "artist": artist_name,
                    "type": r_type,
                    "track_id": album["id"],
                    "first_song": album["id"]
                })

    # Save
    with open(RELEASES_FILE, "w") as f:
        json.dump(releases, f, indent=2)

    return releases

# ==== STEP 3: Create playlist & add songs ====
def create_playlist_with_releases(releases):
    if not releases:
        print("No new releases found.")
        return None

    today = datetime.datetime.now().strftime("%m/%d/%y")
    user_id = sp.current_user()["id"]
    playlist = sp.user_playlist_create(user=user_id,
                                       name=f"new releases - {today}",
                                       public=False)

    track_ids = []
    for r in releases:
        album_tracks = sp.album_tracks(r["track_id"])
        first_track_id = album_tracks["items"][0]["id"]
        track_ids.append(first_track_id)

    sp.playlist_add_items(playlist["id"], track_ids)
    return playlist["external_urls"]["spotify"]

# ==== STEP 4: Send SMS ====
def send_sms(releases, playlist_url):
    if not releases:
        return

    today = datetime.datetime.now().strftime("%m/%d/%y")
    message_body = f"Your new release list for {today} has been generated!\n\n"
    for i, r in enumerate(releases[:5], start=1):
        message_body += f"{i}. '{r['name']}' by {r['artist']} ({r['type']})\n"

    message_body += f"\nAnd more! Check out the full playlist here: {playlist_url}"

    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message_body,
        from_=TWILIO_PHONE,
        to=MY_PHONE
    )
    print("SMS sent!")

# ==== MAIN ====
if __name__ == "__main__":
    artists_data = update_artists_file()
    releases = check_new_releases(artists_data)
    playlist_url = create_playlist_with_releases(releases)
    if playlist_url:
        send_sms(releases, playlist_url)
