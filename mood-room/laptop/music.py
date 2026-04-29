import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="5ac318686f3e4d229b1005bd6d8fdfe5",
    client_secret="6876b6ea15e5406783035f8df4f86627",
    redirect_uri="http://127.0.0.1:9999/callback",
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
        print(f"Same emotion — skipping")
        return

    try:
        devices = sp.devices()
        if not devices['devices']:
            print("No active Spotify device!")
            return

        device_id = devices['devices'][0]['id']

        if emotion == "off":
            try:
                sp.pause_playback(device_id=device_id)
                print("Paused!")
            except:
                # Free account — just reset tracking
                print("Cannot pause — free account")
            current_playlist_emotion = None
            return

        playlist_uri = PLAYLISTS.get(emotion, PLAYLISTS["neutral"])
        
        # Play with shuffle so it's random every time!
        sp.shuffle(True, device_id=device_id)
        sp.start_playback(device_id=device_id, context_uri=playlist_uri)
        
        current_playlist_emotion = emotion
        print(f"Switched to: {emotion} playlist (shuffled)")

    except Exception as e:
        print(f"Spotify error: {e}")