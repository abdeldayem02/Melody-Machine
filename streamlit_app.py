import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import random
import streamlit as st

# Load environment variables from .env file
load_dotenv('.env')

# Access API keys from .env file
api_key = os.getenv('API_KEY')
secret_key = os.getenv('SECRET_KEY')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI', "http://localhost:8501")

# Spotify authentication setup
auth_manager = SpotifyOAuth(
    client_id=api_key,
    client_secret=secret_key,
    redirect_uri=redirect_uri,
    scope="playlist-modify-public user-library-read",
    cache_path=".spotify_token_cache"  # Cache to prevent repeated authorization prompts
)

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=auth_manager)

# Define mood features
mood_features = {
    "happy": {"danceability": random.uniform(0.502,0.730), "energy":random.uniform(0.615,0.865),"valence":random.uniform(0.361,0.742),"loudness":random.uniform(-8.043,-4.20),
              "acousticness":random.uniform(0.011,0.202),"speechiness":random.uniform(0.0381,0.11),"tempo":random.uniform(100.55,142.40)},
    "sad": {"danceability": random.uniform(0.211,0.539), "energy": random.uniform(0.0489,0.261),"valence":random.uniform(0.0548,0.323),"loudness":random.uniform(-25.438,-15.531),"acousticness":random.uniform(0.6,0.9),"instrumentalness":random.uniform(0.7,0.98),"speechiness":random.uniform(0.0367,0.351),"tempo":random.uniform(78.6,129.227)},
    "calm": {"danceability":random.uniform(0.422,0.648), "energy":random.uniform(0.241,0.5),"valence":random.uniform(0.225,0.6),"loudness":random.uniform(-13.824,-8.264),"acousticness":random.uniform(0.589,0.869),"tempo":random.uniform(90,134.43)},
    "energetic": {"danceability":random.uniform(0.466,0.72), "energy": random.uniform(0.554,0.882),"valence":random.uniform(0.17,0.613),"loudness":random.uniform(-11.124,-6.513),"acousticness":random.uniform(0,0.2),"instrumentalness":random.uniform(0.6,0.9),"tempo":random.uniform(107,140)}
}

# Function to search for artists
def search_artist(query):
    results = sp.search(q=query, type='artist', limit=5)
    return results['artists']['items']

# Function to create a playlist with recommendations based on mood and selected artists
def create_playlist(user_id, mood, artist_ids):
    selected_features = mood_features[mood]

    # Create a new playlist
    playlist = sp.user_playlist_create(user_id, f"{mood.capitalize()} Mood Playlist", public=True)
    playlist_id = playlist['id']

    # Prepare the parameters for recommendations, only add features if they exist
    recommendation_params = {
        "seed_artists": artist_ids[:5],  # Up to 5 artists allowed
        "limit": 20
    }

    # Add audio features if they exist in the selected mood features
    for feature in ['danceability', 'energy', 'valence', 'loudness', 'acousticness', 'speechiness', 'tempo']:
        if feature in selected_features:
            recommendation_params[f"target_{feature}"] = selected_features[feature]

    # Get recommendations using available audio features and selected artists
    recommendations = sp.recommendations(**recommendation_params)

    # Extract track URIs from recommendations
    track_uris = [track['uri'] for track in recommendations['tracks']]

    # Add recommended tracks to the playlist
    if track_uris:
        sp.playlist_add_items(playlist_id, track_uris)
        return f"Playlist created and added to your Spotify profile! Playlist ID: {playlist_id}"
    else:
        return "No tracks found matching the mood criteria."

# Streamlit app
def main():
    st.title("Spotify Mood Playlist Creator")

    # Authenticate and get the user info
    user = sp.current_user()
    user_id = user['id']
    st.write(f"Logged in as {user['display_name']}")

    # Mood selection
    mood = st.selectbox("Choose your mood", options=list(mood_features.keys()))

    # Artist search
    query = st.text_input("Search for an artist")
    if st.button("Search"):
        if query:
            artists = search_artist(query)
            if artists:
                artist_names = [artist['name'] for artist in artists]
                artist_selection = st.multiselect("Select artists", options=artist_names)
                artist_ids = [artists[i]['id'] for i in range(len(artists)) if artists[i]['name'] in artist_selection]
            else:
                st.write("No artists found.")
        else:
            st.write("Please enter an artist name.")

    if st.button("Create Playlist"):
        if artist_ids:
            result = create_playlist(user_id, mood, artist_ids)
            st.write(result)
        else:
            st.write("No artists selected.")

if __name__ == "__main__":
    main()
