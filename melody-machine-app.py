import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import random
import logging

# Load environment variables from .env file
load_dotenv('.env')

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Access API keys from .env file
api_key = os.getenv('API_KEY')
secret_key = os.getenv('SECRET_KEY')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

# Spotify authentication setup
scope = "playlist-modify-public user-library-read"

# Initialize OAuth manager and handle access tokens in session state
def get_auth_manager():
    if 'token_info' not in st.session_state:
        sp_oauth = SpotifyOAuth(
            client_id=api_key,
            client_secret=secret_key,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=None  # Disable shared cache file
        )
        auth_url = sp_oauth.get_authorize_url()
        st.write(f"[Click here to authorize with Spotify]({auth_url})")
        
        # Get authorization code
        code = st.experimental_get_query_params().get('code')
        if code:
            token_info = sp_oauth.get_access_token(code)
            st.session_state.token_info = token_info
            st.success("Logged in successfully!")
    return st.session_state.get('token_info')


# Initialize Spotify client
def init_spotify_client(token_info):
    if token_info:
        return spotipy.Spotify(auth=token_info['access_token'])
    return None

# Function to refresh access token if it is expired
def refresh_token_if_needed(sp_oauth):
    if sp_oauth.is_token_expired(st.session_state.token_info):
        st.session_state.token_info = sp_oauth.refresh_access_token(st.session_state.token_info['refresh_token'])

# Define mood features
mood_features = {
    "happy": {"danceability": random.uniform(0.502, 0.730), "energy": random.uniform(0.615, 0.865), "valence": random.uniform(0.361, 0.742),
              "loudness": random.uniform(-8.043, -4.20), "acousticness": random.uniform(0.011, 0.202), "tempo": random.uniform(100.55, 142.40)},
    "sad": {"danceability": random.uniform(0.211, 0.539), "energy": random.uniform(0.0489, 0.261), "valence": random.uniform(0.0548, 0.323),
            "loudness": random.uniform(-25.438, -15.531), "acousticness": random.uniform(0.6, 0.9), "instrumentalness": random.uniform(0.7, 0.98),
            "tempo": random.uniform(78.6, 129.227)},
    "calm": {"danceability": random.uniform(0.422, 0.648), "energy": random.uniform(0.241, 0.5), "valence": random.uniform(0.225, 0.6),
             "loudness": random.uniform(-13.824, -8.264), "acousticness": random.uniform(0.589, 0.869), "tempo": random.uniform(90, 134.43)},
    "energetic": {"danceability": random.uniform(0.466, 0.72), "energy": random.uniform(0.554, 0.882), "valence": random.uniform(0.17, 0.613),
                  "loudness": random.uniform(-11.124, -6.513), "acousticness": random.uniform(0, 0.2), "instrumentalness": random.uniform(0.6, 0.9),
                  "tempo": random.uniform(107, 140)}
}

# Function to search for artists
def search_artist(sp, query):
    results = sp.search(q=query, type='artist')
    if results['artists']['items']:
        first_artist = results['artists']['items'][0]
        name = first_artist.get('name', 'Unknown Artist')
        artist_id = first_artist.get('id', None)
        return [{'name': name, 'id': artist_id}]
    return []

# Function to create a playlist
def create_playlist(sp, user_id, mood, artist_ids, num_songs):
    selected_features = mood_features[mood]
    artist_names = [sp.artist(artist_id)['name'] for artist_id in artist_ids[:5]]
    artist_names_str = ", ".join(artist_names)

    playlist_description = f"A playlist for the {mood} mood featuring artists: {artist_names_str}"
    playlist = sp.user_playlist_create(user_id, f"{mood.capitalize()} Mood Playlist", public=True, description=playlist_description)
    playlist_id = playlist['id']

    recommendation_params = {
        "seed_artists": artist_ids[:5], 
        "limit": num_songs  # Use the number of songs chosen by the user
    }

    for feature in ['danceability', 'energy', 'valence', 'loudness', 'acousticness', 'speechiness', 'tempo']:
        if feature in selected_features:
            recommendation_params[f"target_{feature}"] = selected_features[feature]

    recommendations = sp.recommendations(**recommendation_params)
    track_uris = [track['uri'] for track in recommendations['tracks']]

    if track_uris:
        sp.playlist_add_items(playlist_id, track_uris)
        st.success(f"Playlist created and added to your Spotify profile! Playlist ID: {playlist_id}")
    else:
        st.error("No tracks found matching the mood criteria.")


# Streamlit app interface
def main():
    st.title("Spotify Mood Playlist Generator")
    
    # Handle authentication and token management
    token_info = get_auth_manager()
    if token_info:
        sp_oauth = SpotifyOAuth(client_id=api_key, client_secret=secret_key, redirect_uri=redirect_uri, scope=scope, cache_path=None)
        refresh_token_if_needed(sp_oauth)
        sp = init_spotify_client(token_info)
        
        if sp:
            user = sp.current_user()
            user_id = user['id']
            with st.sidebar:
                pfp_url = user['images'][0]['url'] if user['images'] else None
                if pfp_url:
                    st.image(pfp_url, width=200)
                st.write(f"Logged in as {user['display_name']}")
                st.write(f"Followers: {user['followers']['total']}")

            # Mood selection
            mood = st.selectbox("Choose your mood", ["happy", "sad", "calm", "energetic"])
            
            # Initialize lists in session state
            if 'artist_ids' not in st.session_state:
                st.session_state.artist_ids = []
            if 'artist_names' not in st.session_state:
                st.session_state.artist_names = []

            # Modify the input handling
            artist_name_input = st.text_input("Search for an artist [up to 5 artists]:  (type 'done' when finished)")

            if artist_name_input and artist_name_input.lower() != 'done':
                artists = search_artist(sp, artist_name_input)
                if artists:
                    artist = artists[0]
                    st.write(f"Artist: {artist['name']}")
                    
                    # Get and display artist image if available
                    artist_info = sp.artist(artist['id'])
                    if artist_info['images']:
                        image_url = artist_info['images'][0]['url']  # Get the first image
                        st.image(image_url, width=200)  # Display the image
                    else:
                        st.write("No image available for this artist.")
                    
                    # Add artist to session state
                    if artist['id']:
                        st.session_state.artist_ids.append(artist['id'])
                        st.session_state.artist_names.append(artist['name'])
                        st.write(f"Added {artist['name']} to the selection.")
                else:
                    st.write("No artists found.")

            # If 'done' is typed, display the selected artists
            if artist_name_input.lower() == 'done':
                if st.session_state.artist_names:
                    st.write("Selected Artists:")
                    for artist in st.session_state.artist_names:
                        st.write(artist)
                else:
                    st.write("No artists selected.")

            # Add a slider for choosing the number of songs in the playlist
            num_songs = st.slider("Select the number of songs", min_value=1, max_value=100, value=20)

            # Button to create the playlist
            if st.button("Create Playlist") and st.session_state.artist_ids:
                create_playlist(sp, user_id, mood, st.session_state.artist_ids, num_songs)
                
                # Clear the lists after playlist creation
                st.session_state.artist_ids = []
                st.session_state.artist_names = []
if __name__ == "__main__":
    main()
