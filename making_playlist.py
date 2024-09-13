import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
from dotenv import load_dotenv
import os
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from .env file
load_dotenv('.env')

# Access API keys from .env file
api_key = os.getenv('API_KEY')
secret_key = os.getenv('SECRET_KEY')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI', "http://localhost:8501")

# Initialize session state
if 'sp' not in st.session_state:
    st.session_state.sp = None
if 'selected_artists' not in st.session_state:
    st.session_state.selected_artists = []

# Spotify authentication setup
auth_manager = SpotifyOAuth(
    client_id=api_key,
    client_secret=secret_key,
    redirect_uri=redirect_uri,
    scope="playlist-modify-public user-library-read"
)

# Handle OAuth redirection
if 'code' in st.query_params:
    try:
        st.session_state.sp = spotipy.Spotify(auth_manager=auth_manager)
        st.query_params.clear()  # Clear query parameters to avoid redirect loops
        st.success("Successfully authenticated with Spotify!")
    except Exception as e:
        st.error(f"Authorization failed. Error: {e}")
elif st.session_state.sp is None:
    auth_url = auth_manager.get_authorize_url()
    st.markdown(f"[Authorize Spotify Access]({auth_url})")

# Mood selection and playlist creation logic
if st.session_state.sp:
    # Mood selection
    mood = st.selectbox("Choose your mood", ["happy", "sad", "calm", "energetic"])
    mood_features = {
        "happy": {"danceability": 0.8, "energy": 0.7},
        "sad": {"danceability": 0.3, "energy": 0.2},
        "calm": {"danceability": 0.4, "energy": 0.3},
        "energetic": {"danceability": 0.7, "energy": 0.9}
    }
    selected_features = mood_features[mood]

    # Artist search function
    def search_artist(query):
        if st.session_state.sp:
            results = st.session_state.sp.search(q=query, type='artist', limit=5)
            return results['artists']['items']
        return []

    # Form to search and select artists
    with st.form(key="artist_search_form"):
        query = st.text_input("Search for artists")
        submit_button = st.form_submit_button(label="Search")

        if submit_button and query:
            artists = search_artist(query)
            st.session_state.search_results = artists  # Save search results in session state
        else:
            artists = st.session_state.search_results if 'search_results' in st.session_state else []

        for artist in artists:
            if st.checkbox(artist['name'], key=artist['id']):
                if artist['id'] not in st.session_state.selected_artists:
                    st.session_state.selected_artists.append(artist['id'])

    # Display selected artists
    st.write("Selected Artists:")
    for artist_id in st.session_state.selected_artists:
        artist = st.session_state.sp.artist(artist_id)
        st.write(artist['name'])

    # Create playlist
    if st.button("Create my playlist"):
        if st.session_state.selected_artists:
            user_id = st.session_state.sp.current_user()['id']
            playlist = st.session_state.sp.user_playlist_create(user_id, "Mood Playlist", public=True)
            playlist_id = playlist['id']

            # Search for tracks based on mood and artists
            track_uris = []
            for artist_id in st.session_state.selected_artists:
                results = st.session_state.sp.artist_top_tracks(artist_id)
                for track in results['tracks']:
                    track_features = st.session_state.sp.audio_features(track['id'])[0]
                    if track_features and \
                       (selected_features['danceability'] - 0.1 <= track_features['danceability'] <= selected_features['danceability'] + 0.1) and \
                       (selected_features['energy'] - 0.1 <= track_features['energy'] <= selected_features['energy'] + 0.1):
                        track_uris.append(track['uri'])

            # Add tracks to the playlist
            if track_uris:
                st.session_state.sp.playlist_add_items(playlist_id, track_uris)
                st.success("Playlist created and added to your Spotify profile!")
            else:
                st.warning("No tracks found matching the mood criteria.")
        else:
            st.warning("Please select at least one artist.")
