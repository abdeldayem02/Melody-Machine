# Melody-Machine
A music recommendation system that generates mood-based playlists using Spotify.

## Description
Melody-Machine is a web application that allows users to create personalized playlists based on their mood. It integrates with Spotify to fetch user data, recommend tracks, and create playlists. Users can search for artists, select a mood, and generate playlists tailored to their preferences.

## Features
- **Mood-Based Playlists**: Generate playlists for moods like happy, sad, calm, and energetic.
- **Artist Search**: Search and add up to 5 artists to influence playlist recommendations.
- **Customizable Playlist Size**: Choose the number of songs in the playlist (up to 100).
- **Spotify Integration**: Log in with Spotify to access your account and create playlists directly.

## Technologies Used
- **Backend**: Flask for API and server-side logic.
- **Frontend**: HTML, CSS (Bootstrap), and Jinja2 templates.
- **Spotify API**: Spotipy library for interacting with Spotify.
- **Streamlit**: For an alternative interactive interface.
- **Environment Management**: Python-dotenv for managing environment variables.

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd Melody-Machine2
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up a `.env` file with the following variables:
   ```
   API_KEY=<your-spotify-client-id>
   SECRET_KEY=<your-spotify-client-secret>
   SPOTIPY_REDIRECT_URI=<your-redirect-uri>
   ```

## Usage
### Flask Application
1. Run the Flask app:
   ```
   python Flask_app.py
   ```
2. Open your browser and navigate to `http://127.0.0.1:5000`.

### Streamlit Application
1. Run the Streamlit app:
   ```
   streamlit run melody-machine-app.py
   ```
2. Follow the instructions in the Streamlit interface.

## File Structure
- **templates/**: HTML templates for the Flask app.
- **playlist creation.py**: Core logic for playlist creation and artist search.
- **melody-machine-app.py**: Streamlit-based interface for the application.
- **Flask_app.py**: Flask-based backend for the application.
- **requirements.txt**: Python dependencies.

## License
This project is licensed under the MIT License.
