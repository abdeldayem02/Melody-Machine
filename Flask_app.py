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

# Mood features dictionary remains the same
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
        artist_name = request.form.get('artist_name')
        results = sp.search(q=artist_name, type='artist', limit=1)
        
        if results['artists']['items']:
            artist_info = results['artists']['items'][0]
            artist_id = artist_info['id']
            artist_name = artist_info['name']
            artist_image = artist_info['images'][0]['url'] if artist_info['images'] else None

            session.setdefault('artist_ids', []).append(artist_id)
            session['artist_name'] = artist_name

            return render_template('home.html', artist_name=artist_name, artist_image=artist_image)
        else:
            return render_template('home.html', error="Artist not found.")
    except Exception as e:
        logging.error(f"Search artist error: {e}")
        return redirect(url_for('login'))

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    sp = get_spotify_client()
    if not sp or not session.get('artist_ids'):
        return redirect(url_for('login'))
    
    try:
        mood = request.form['mood']
        num_songs = int(request.form['num_songs'])
        user_id = sp.current_user()['id']
        selected_features = mood_features[mood]
        artist_ids = session.get('artist_ids')
        
        playlist = sp.user_playlist_create(user_id, f"{mood.capitalize()} Mood Playlist", public=True)
        playlist_id = playlist['id']
        
        recommendation_params = {
            "seed_artists": artist_ids[:5],
            "limit": num_songs
        }
        
        for feature, value in selected_features.items():
            recommendation_params[f"target_{feature}"] = value

        recommendations = sp.recommendations(**recommendation_params)
        track_uris = [track['uri'] for track in recommendations['tracks']]

        if track_uris:
            sp.playlist_add_items(playlist_id, track_uris)
            session['artist_ids'] = []
            return render_template('success.html', playlist_id=playlist_id)
        
        return render_template('home.html', error="No tracks found for the given criteria.")
    except Exception as e:
        logging.error(f"Create playlist error: {e}")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)