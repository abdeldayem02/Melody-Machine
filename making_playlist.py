import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
# Load environment variables from .env file


# Access API keys
api_key = os.getenv('API_KEY')
secret_key = os.getenv('SECRET_KEY')

# Spotify authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=api_key,
    client_secret=secret_key,
    scope="playlist-modify-public user-library-read"
))

# Mood selection
mood = st.selectbox("Choose your mood", ["happy", "sad", "calm", "energetic"])
mood_features = {
    "happy": {"danceability": 0.8, "energy": 0.7},
    "sad": {"danceability": 0.3, "energy": 0.2},
    "calm": {"danceability": 0.4, "energy": 0.3},
    "energetic": {"danceability": 0.7, "energy": 0.9}
}
selected_features = mood_features[mood]

# Artist search
selected_artists = []
def search_artist(query):
    results = sp.search(q=query, type='artist', limit=5)
    return results['artists']['items']

query = st.text_input("Search for artists")
if query:
    artists = search_artist(query)
    for artist in artists:
        if st.button(artist['name']):
            selected_artists.append(artist['id'])

# Create playlist
if st.button("Create my playlist"):
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user_id, "Mood Playlist", public=True)
    playlist_id = playlist['id']

    # Example of adding tracks based on mood features
    results = sp.search(q=f"danceability:{selected_features['danceability']} energy:{selected_features['energy']}", type='track', limit=20)
    tracks = [track['uri'] for track in results['tracks']['items']]
    sp.playlist_add_items(playlist_id, tracks)

    st.success("Playlist created and added to your Spotify profile!")
