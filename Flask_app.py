from flask import Flask, request, redirect, session, url_for, render_template
import spotipy 
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheHandler
from dotenv import load_dotenv
import os
import random
import logging
import time

# Load environment variables from .env file
load_dotenv('.env')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Spotify API setup
api_key = os.getenv('API_KEY')
secret_key = os.getenv('SECRET_KEY')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
scope = "playlist-modify-public user-library-read"

# Logging setup
logging.basicConfig(level=logging.DEBUG)

# Original mood features dictionary (for reference)
# mood_features = {
#     "happy": {"danceability": random.uniform(0.502, 0.730), "energy": random.uniform(0.615, 0.865), 
#               "valence": random.uniform(0.361, 0.742), "loudness": random.uniform(-8.043, -4.20), 
#               "acousticness": random.uniform(0.011, 0.202), "tempo": random.uniform(100.55, 142.40)},
#     "sad": {"danceability": random.uniform(0.211, 0.539), "energy": random.uniform(0.0489, 0.261), 
#             "valence": random.uniform(0.0548, 0.323), "loudness": random.uniform(-25.438, -15.531), 
#             "acousticness": random.uniform(0.6, 0.9), "instrumentalness": random.uniform(0.7, 0.98),
#             "tempo": random.uniform(78.6, 129.227)},
#     "calm": {"danceability": random.uniform(0.422, 0.648), "energy": random.uniform(0.241, 0.5), 
#              "valence": random.uniform(0.225, 0.6), "loudness": random.uniform(-13.824, -8.264), 
#              "acousticness": random.uniform(0.589, 0.869), "tempo": random.uniform(90, 134.43)},
#     "energetic": {"danceability": random.uniform(0.466, 0.72), "energy": random.uniform(0.554, 0.882), 
#                   "valence": random.uniform(0.17, 0.613), "loudness": random.uniform(-11.124, -6.513), 
#                   "acousticness": random.uniform(0, 0.2), "instrumentalness": random.uniform(0.6, 0.9),
#                   "tempo": random.uniform(107, 140)}
# }

# Current mood features dictionary with wider ranges
mood_features = {
    "happy": {
        "danceability": random.uniform(0.4, 0.9),    # Wider range for danceability
        "energy": random.uniform(0.5, 0.95),         # Higher energy range
        "valence": random.uniform(0.5, 0.95),        # Higher valence range
        "acousticness": random.uniform(0.0, 0.4),    # Lower acousticness for happy songs
        "tempo": random.uniform(95, 150)             # Wider tempo range
    },
    "sad": {
        "danceability": random.uniform(0.2, 0.5),    # Lower danceability range
        "energy": random.uniform(0.1, 0.4),          # Lower energy range
        "valence": random.uniform(0.1, 0.4),         # Lower valence range
        "acousticness": random.uniform(0.5, 0.95),   # Higher acousticness
        "instrumentalness": random.uniform(0.3, 0.8), # Moderate to high instrumentalness
        "tempo": random.uniform(60, 100)             # Slower tempo range
    },
    "calm": {
        "danceability": random.uniform(0.3, 0.6),    # Moderate danceability
        "energy": random.uniform(0.2, 0.5),          # Lower energy
        "valence": random.uniform(0.3, 0.7),         # Wider valence range
        "acousticness": random.uniform(0.5, 0.95),   # Higher acousticness
        "tempo": random.uniform(70, 110)             # Moderate tempo range
    },
    "energetic": {
        "danceability": random.uniform(0.6, 0.9),    # Higher danceability
        "energy": random.uniform(0.7, 0.95),         # High energy
        "valence": random.uniform(0.4, 0.9),         # Wider valence range
        "acousticness": random.uniform(0.0, 0.3),    # Lower acousticness
        "tempo": random.uniform(120, 160)            # Higher tempo range
    }
}

class SessionCacheHandler(CacheHandler):
    def __init__(self, session):
        self.session = session

    def get_cached_token(self):
        token_info = self.session.get('token_info', None)
        return token_info

    def save_token_to_cache(self, token_info):
        self.session['token_info'] = token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=api_key,
        client_secret=secret_key,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_handler=SessionCacheHandler(session)
    )

def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None

    # Check if token needs refresh
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60

    if is_expired:
        sp_oauth = create_spotify_oauth()
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
        except Exception as e:
            logging.error(f"Token refresh error: {e}")
            return None
    
    return token_info

def get_spotify_client():
    token_info = get_token()
    if token_info:
        return spotipy.Spotify(auth=token_info['access_token'])
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # Clear any existing session data
    session.clear()
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        sp_oauth = create_spotify_oauth()
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            logging.error(f"Authorization error: {error}")
            return redirect(url_for('index'))
            
        token_info = sp_oauth.get_access_token(code)
        session['token_info'] = token_info
        return redirect(url_for('home'))
    except Exception as e:
        logging.error(f"Callback error: {e}")
        return redirect(url_for('login'))

@app.route('/home')
def home():
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for('login'))
    
    try:
        user = sp.current_user()
        user_id = user['id']
        pfp_url = user['images'][0]['url'] if user['images'] else None
        return render_template('home.html', user_name=user['display_name'], user_id=user_id, pfp_url=pfp_url)
    except Exception as e:
        logging.error(f"Home page error: {e}")
        return redirect(url_for('login'))

@app.route('/search_artist', methods=['POST'])
def search_artist():
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for('login'))
    
    try:
        # Get current user info
        user = sp.current_user()
        user_id = user['id']
        user_name = user['display_name']
        pfp_url = user['images'][0]['url'] if user['images'] else None
        
        artist_name = request.form.get('artist_name')
        results = sp.search(q=artist_name, type='artist', limit=1)
        
        # Initialize artists list in session if it doesn't exist
        if 'added_artists' not in session:
            session['added_artists'] = []

        if results['artists']['items']:
            artist_info = results['artists']['items'][0]
            artist_id = artist_info['id']
            artist_name = artist_info['name']
            artist_image = artist_info['images'][0]['url'] if artist_info['images'] else None

            # Store artist info in session
            session.setdefault('artist_ids', []).append(artist_id)
            session['added_artists'].append({
                'name': artist_name,
                'image': artist_image
            })

            return render_template('home.html', 
                                user_name=user_name,
                                user_id=user_id,
                                pfp_url=pfp_url,
                                added_artists=session['added_artists'])
        else:
            return render_template('home.html',
                                user_name=user_name,
                                user_id=user_id,
                                pfp_url=pfp_url,
                                added_artists=session['added_artists'],
                                error="Artist not found.")
    except Exception as e:
        logging.error(f"Search artist error: {e}")
        return redirect(url_for('login'))

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for('login'))
    
    try:
        # Get current user info for rendering
        user = sp.current_user()
        user_id = user['id']
        user_name = user['display_name']
        pfp_url = user['images'][0]['url'] if user['images'] else None
        
        if not session.get('artist_ids'):
            return render_template('home.html',
                                user_name=user_name,
                                user_id=user_id,
                                pfp_url=pfp_url,
                                added_artists=session.get('added_artists', []),
                                error="Please add at least one artist before creating a playlist.")
        
        mood = request.form['mood']
        num_songs = min(int(request.form['num_songs']), 100)  # Limit to 100 songs
        selected_features = mood_features[mood].copy()  # Create a copy to avoid modifying the original
        artist_ids = session.get('artist_ids', [])[:5]  # Get up to 5 artists
        
        logging.info(f"Creating playlist with mood: {mood}, num_songs: {num_songs}, artists: {artist_ids}")
        
        # Create the playlist
        playlist_name = f"{mood.capitalize()} Mood Playlist - {', '.join([artist['name'] for artist in session.get('added_artists', [])])}"
        playlist = sp.user_playlist_create(user_id, playlist_name, public=True)
        playlist_id = playlist['id']
        
        # Prepare recommendation parameters with valid features only
        valid_features = ["danceability", "energy", "valence", "acousticness", "instrumentalness", "tempo"]
        recommendation_params = {
            "seed_artists": artist_ids,
            "limit": num_songs
        }
        
        # Add target features for the mood
        for feature, value in selected_features.items():
            if feature in valid_features:
                if feature == "tempo":
                    # Spotify expects tempo as is
                    recommendation_params[f"target_{feature}"] = value
                else:
                    # Ensure other features are between 0 and 1
                    recommendation_params[f"target_{feature}"] = max(0.0, min(1.0, value))
        
        logging.info(f"Recommendation parameters: {recommendation_params}")
        
        # Get recommendations
        try:
            recommendations = sp.recommendations(**recommendation_params)
            if not recommendations['tracks']:
                logging.error("No tracks returned from recommendations API")
                raise Exception("No tracks found in recommendations")
            
            track_uris = [track['uri'] for track in recommendations['tracks']]
            logging.info(f"Got {len(track_uris)} track recommendations")
            
            if track_uris:
                # Add tracks in batches of 100 (Spotify API limit)
                for i in range(0, len(track_uris), 100):
                    batch = track_uris[i:i + 100]
                    sp.playlist_add_items(playlist_id, batch)
                    logging.info(f"Added batch of {len(batch)} tracks to playlist")
                
                # Clear the artist lists after successful playlist creation
                session['artist_ids'] = []
                session['added_artists'] = []
                
                # Get the playlist URL and verify tracks were added
                playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
                playlist_tracks = sp.playlist_items(playlist_id)
                if not playlist_tracks['items']:
                    raise Exception("Tracks were not properly added to the playlist")
                
                logging.info(f"Successfully created playlist with {len(playlist_tracks['items'])} tracks")
                return render_template('success.html', 
                                    playlist_id=playlist_id,
                                    playlist_url=playlist_url,
                                    user_name=user_name,
                                    user_id=user_id,
                                    pfp_url=pfp_url)
            else:
                raise Exception("No tracks found in recommendations")
                
        except Exception as e:
            logging.error(f"Recommendation error: {str(e)}")
            return render_template('home.html',
                                user_name=user_name,
                                user_id=user_id,
                                pfp_url=pfp_url,
                                added_artists=session.get('added_artists', []),
                                error=f"Error getting recommendations: {str(e)}")
                
    except Exception as e:
        logging.error(f"Create playlist error: {str(e)}")
        return render_template('home.html',
                            user_name=user_name,
                            user_id=user_id,
                            pfp_url=pfp_url,
                            added_artists=session.get('added_artists', []),
                            error=f"Error creating playlist: {str(e)}")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)