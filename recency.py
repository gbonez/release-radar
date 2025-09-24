import os
import datetime
from collections import defaultdict
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

# ==== CONFIGURATION ====
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = (os.environ.get("BASE_URL") or "http://localhost:5000") + "/callback"

# Scope includes reading your saved tracks
scope = "user-library-read"

sp = Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=scope
))

# ==== PARAMETERS ====
DECAY = 0.9  # how much older tracks count less
LOOKBACK_DAYS = 180  # ~6 months
TOP_N_ARTISTS = 100

cutoff_date = datetime.datetime.now() - datetime.timedelta(days=LOOKBACK_DAYS)

artist_scores = defaultdict(float)

# Spotify API paginates saved tracks 50 at a time
limit = 50
offset = 0
total_tracks_processed = 0

while True:
    results = sp.current_user_saved_tracks(limit=limit, offset=offset)
    items = results["items"]
    if not items:
        break

    print(f"\nProcessing batch starting at offset {offset} ({len(items)} tracks)...")

    for item in items:
        total_tracks_processed += 1
        track = item["track"]
        added_at_str = item["added_at"]  # ISO 8601 timestamp
        added_at = datetime.datetime.strptime(added_at_str, "%Y-%m-%dT%H:%M:%SZ")

        if added_at < cutoff_date:
            continue  # skip tracks older than 6 months

        days_ago = (datetime.datetime.now() - added_at).days
        weight = DECAY ** (days_ago / 30)  # monthly decay

        for artist in track["artists"]:
            artist_id = artist["id"]
            artist_name = artist["name"]
            artist_scores[(artist_id, artist_name)] += weight
            print(f"Added weight {weight:.3f} for artist: {artist_name} (track added {days_ago} days ago)")

    print(f"Finished processing batch. Total tracks processed so far: {total_tracks_processed}")
    offset += limit

# Sort artists by descending score
sorted_artists = sorted(artist_scores.items(), key=lambda x: x[1], reverse=True)[:TOP_N_ARTISTS]

print(f"\nTop {TOP_N_ARTISTS} artists in the last {LOOKBACK_DAYS} days (weighted by recency):")
for i, ((artist_id, artist_name), score) in enumerate(sorted_artists, start=1):
    print(f"{i}. {artist_name} (score={score:.2f})")
