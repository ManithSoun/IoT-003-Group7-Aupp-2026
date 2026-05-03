import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id= os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret= os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri= os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-modify-playback-state user-read-playback-state",
    open_browser=True,
    cache_path=".spotify_cache"
))

PLAYLISTS = {
    "happy":    "spotify:playlist:0D327uChQL23ztWH2CHNdh",
    "sad":      "spotify:playlist:04s3sXceiWauXzBPOqfxOX",
    "angry":    "spotify:playlist:7vlxHyLBgE8EuBcZxYZyzj",
    "neutral":  "spotify:playlist:0EOuwNPYzMfcemIbHoqqrj",
    "surprise": "spotify:playlist:6MvK7J7PrO3TiNZg10tPhL",
    "fear":     "spotify:playlist:3yoKElJYbFz1B140ZqClCh",
}

current_playlist_emotion = None 

def play_playlist(emotion):
    global current_playlist_emotion

    print(f"play_playlist called: {emotion} (current: {current_playlist_emotion})")

    if emotion == current_playlist_emotion:
        print(f"Same — skipping")
        return

    try:
        devices = sp.devices()
        if not devices['devices']:
            print("No Spotify device!")
            return

        device_id = devices['devices'][0]['id']

        if emotion == "off":
            try:
                sp.pause_playback(device_id=device_id)
                print("Paused!")
            except Exception as e:
                print(f"Cannot pause: {e}")
            current_playlist_emotion = None
            return

        playlist_uri = PLAYLISTS.get(emotion, PLAYLISTS["neutral"])
        sp.shuffle(True, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=playlist_uri)
        current_playlist_emotion = emotion
        print(f"Playing: {emotion}")

    except Exception as e:
        print(f"Spotify error: {e}")

def reset_playlist():
    global current_playlist_emotion
    current_playlist_emotion = None
    print("Playlist reset!")