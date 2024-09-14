import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import logging
import random
# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from .env file
load_dotenv('.env')

# Access API keys from .env file
api_key = os.getenv('API_KEY')
secret_key = os.getenv('SECRET_KEY')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

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
    "happy": {"danceability": random.uniform(0.502,0.730), "energy":random.uniform(0.615,0.865),"valence":random.uniform(0.361,0.742),
              "loudness":random.uniform(-8.043,-4.20),"acousticness":random.uniform(0.011,0.202),"tempo":random.uniform(100.55,142.40)},
    "sad": {"danceability": random.uniform(0.211,0.539), "energy": random.uniform(0.0489,0.261),"valence":random.uniform(0.0548,0.323),
            "loudness":random.uniform(-25.438,-15.531),"acousticness":random.uniform(0.6,0.9),"instrumentalness":random.uniform(0.7,0.98),
            "tempo":random.uniform(78.6,129.227)},
    "calm": {"danceability":random.uniform(0.422,0.648), "energy":random.uniform(0.241,0.5),"valence":random.uniform(0.225,0.6),
             "loudness":random.uniform(-13.824,-8.264),"acousticness":random.uniform(0.589,0.869),"tempo":random.uniform(90,134.43)},
    "energetic": {"danceability":random.uniform(0.466,0.72), "energy": random.uniform(0.554,0.882),"valence":random.uniform(0.17,0.613),
                  "loudness":random.uniform(-11.124,-6.513),"acousticness":random.uniform(0,0.2),"instrumentalness":random.uniform(0.6,0.9),
                  "tempo":random.uniform(107,140)}
}

def search_artist(query):
    # Search for artists based on the query (without specifying limit)
    results = sp.search(q=query, type='artist')
    
    # Return only the first artist in the results
    if results['artists']['items']:
        first_artist = results['artists']['items'][0]
        name = first_artist.get('name', 'Unknown Artist')
        artist_id = first_artist.get('id', None)  # Fallback in case 'id' is missing
        return [{'name': name, 'id': artist_id}]
    
    # Return an empty list if no artist is found
    return []




# Function to create a playlist with recommendations based on mood and selected artists
def create_playlist(user_id, mood, artist_ids):
    selected_features = mood_features[mood]

    # Get artist names for the selected artist IDs
    artist_names = [sp.artist(artist_id)['name'] for artist_id in artist_ids[:5]]  # Fetch names for up to 5 artists

    # Join artist names to include them in the playlist description
    artist_names_str = ", ".join(artist_names)

    # Create a new playlist with mood and artist names in the description
    playlist_description = f"A playlist for the {mood} mood featuring artists: {artist_names_str}"
    playlist = sp.user_playlist_create(user_id, f"{mood.capitalize()} Mood Playlist", public=True, description=playlist_description)
    playlist_id = playlist['id']

    # Prepare the parameters for recommendations, only add features if they exist
    recommendation_params = {
        "seed_artists": artist_ids[:5],  # Up to 5 artists allowed
        "limit": 20 # number of tracks
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
        print(f"Playlist created and added to your Spotify profile! Playlist ID: {playlist_id}")
    else:
        print("No tracks found matching the mood criteria.")


# Main function to handle input and logic
def main():
    # Authenticate and get the user info
    user = sp.current_user()
    user_id = user['id']
    print(f"Logged in as {user['display_name']}")

    # Ask for mood selection
    mood = input("Choose your mood (happy, sad, calm, energetic): ").lower()
    if mood not in mood_features:
        print("Invalid mood selection.")
        return

    artist_ids = []  # List to store selected artist IDs

    while True:
        query = input("Search for an artist (or type 'done' to finish): ")
        
        if query.lower() == 'done':
            break

        artists = search_artist(query)
        
        if artists:
            # Display the top artist result with their popularity
            artist = artists[0]  # Since only one artist is returned
            print(f"Artist: {artist['name']}")
            
            if artist['id']:  # Ensure the artist has an ID
                artist_ids.append(artist['id'])
                print(f"Added {artist['name']} to the selection.")
            else:
                print(f"Artist {artist['name']} does not have a valid ID.")
        else:
            print("No artists found.")



    if artist_ids:
        # Create playlist
        create_playlist(user_id, mood, artist_ids)
    else:
        print("No artists selected.")

if __name__ == "__main__":
    main()
