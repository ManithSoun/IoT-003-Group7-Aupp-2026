import spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID = "client_id"
CLIENT_SECRET = "client_secret"
REDIRECT_URI = "https://127.0.0.1:8888/callback"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-modify-playback-state user-read-playback-state"
))

PLAYLISTS = {
    "happy":    "spotify:playlist:37i9dQZF1DXdPec7aLTmlC",
    "sad":      "spotify:playlist:37i9dQZF1DX3YSRoSdA634",
    "angry":    "spotify:playlist:37i9dQZF1DWXIcbzpLauPS",
    "fear":     "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO",
    "surprise": "spotify:playlist:37i9dQZF1DXdPec7aLTmlC",
    "neutral":  "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO",
}

def play_playlist(emotion):
    try:
        devices = sp.devices()
        if not devices['devices']:
            print("No active Spotify device found!")
            print("Open Spotify on your laptop first.")
            return
        
        device_id = devices['devices'][0]['id']
        playlist_uri = PLAYLISTS.get(emotion, PLAYLISTS["neutral"])
        sp.start_playback(device_id=device_id, context_uri=playlist_uri)
        print(f"Now playing: {emotion} playlist")

    except Exception as e:
        print(f"Spotify error: {e}")

if __name__ == '__main__':
    print("Testing Spotify connection...")
    play_playlist("fear")