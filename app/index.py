'''
This will likely end up being the index.py that serves as the homepage for our Flask
implementation. Right now the entire file structure still needs to be reworked to work
with Flask, but this is the gist of the end-points for the front-end.

This file runs the webscraper, then before running main_captioner.py on the results,
it asks the user to mark whether images are decorative, links, or infographics. It then
modifies the CSV file passed to the main_captioner.py 
'''
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_session import Session
from sys import prefix, base_prefix, executable
from subprocess import CalledProcessError
from shutil import which as shutil_which
from os import name as os_name, urandom, environ
# from json import dumps as json_dumps
from flask_sqlalchemy import SQLAlchemy
# from csv import reader
from string import ascii_letters, digits
from random import choices
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from . import main

app = Flask(__name__)
app.secret_key = environ.get("SECRET_KEY", urandom(24))

# Use Supabase PostgreSQL for session storage
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("SUPABASE_DB_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Use SQLAlchemy session backend
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY_TABLE"] = "flask_sessions"

# Initialize SQLAlchemy and Flask-Session
db = SQLAlchemy(app)
app.config["SESSION_SQLALCHEMY"] = db

Session(app)

load_dotenv()

''' Oauth Setup'''
app.config['SERVER_NAME'] = 'localhost:5000'
oauth = OAuth(app)
''' Oauth Setup '''

'''Finds the correct Python executable: prioritizes virtual environment, otherwise falls back to system Python.'''
def get_python_path():
    # 1. Check if running inside a virtual environment
    if prefix != base_prefix:  
        return executable  # Return the venv's Python path

    # 2. Check if a virtual environment exists in common locations
    possible_venv_dirs = [".venv", "venv", "env"]  # Add other venv folder names if your team uses different ones
    for venv_dir in possible_venv_dirs:
        python_subdir = "Scripts" if os_name == "nt" else "bin"
        python_path = path.join(venv_dir, python_subdir, "python")
        if path.exists(python_path):
            return python_path  # Use the detected virtual environment Python

    # 3. If no virtual environment is found, fall back to system Python
    return shutil_which("python") or shutil_which("python3")


python_path = get_python_path()


'''Main home page'''
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Gets URL entered by the user
        url = request.form.get('url')

        if url:
            try:
                # Runs the web scraper on the given site
                validated_url, site_data = main.web_scraper(url)

                # Store the validated url and list of data tuples in the session
                session["url"] = validated_url
                session["site_data"] = site_data

                return redirect(url_for('annotate'))
                
            except CalledProcessError as e:
                print(f"Error: {e}")
                print(f"Standard Output: {e.stdout}")
                print(f"Standard Error: {e.stderr}")
                return render_template('error.html')

    return render_template('index.html')


'''Page to allow for user annotations of images'''
@app.route('/annotate', methods=['GET', 'POST'])
def annotate():
    # Reads scraped data from session values
    image_links = [data[0] for data in session.get("site_data", None)]

    image_tags = []

    # Default to "don't include" tag if invalid URL
    for image in image_links:
        if image == "true":
            image_tags.append(3)
        else:
            image_tags.append(0)

    return render_template("annotate.html", image_links=image_links, image_tags=image_tags)


'''JSON to process annotations from user'''
@app.route('/process_images', methods=['GET', 'POST'])
def process_images():
    # Gets the JSON storing the user's image annotations
    data = request.get_json()
    tagged_list = data.get("taggedList", [])

    # Reads data from session values
    site_data = session.get("site_data", None)
    url       = session.get("url", None)
    user_id  = session.get("user_id", None)

    # Generates alt-text for images and stores in session
    generated_data, generation_id, data_ids = main.process_site(site_data, tagged_list, url, user_id)
    session["generated_data"] = generated_data
    session["generation_id"]  = generation_id
    session["data_ids"]       = data_ids

    return redirect(url_for('displayed_images'))


# Page to show images with their alt-text
@app.route('/displayed_images', methods=['GET', 'POST'])
def displayed_images():
    # Reads data from session value
    generated_data = session.get("generated_data", None)
    data_ids       = session.get("data_ids", None)

    return render_template("displayed_images.html", data=generated_data, data_ids=data_ids)


@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"message": "Hello from Flask!", "status": "success"})

''' Oauth Google '''
def generate_nonce():
    return ''.join(choices(ascii_letters + digits, k=16))

@app.route('/google/')
def google():
    nonce = generate_nonce()
    session['nonce'] = nonce
    GOOGLE_CLIENT_ID = environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET_WEB = environ.get('GOOGLE_CLIENT_SECRET')
    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET_WEB,
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
     
    # Redirect to google_auth function
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)
 
@app.route('/google/auth/')
def google_auth():
    token = oauth.google.authorize_access_token()
    nonce = session.pop('nonce', None)
    if not nonce:
        return "Error: No nonce found, possible session timeout", 400
    try:
        user = oauth.google.parse_id_token(token, nonce=nonce)
        print("Google User:", user)
        return redirect('/')
    except Exception as e:
        return f"Error while parsing ID token: {str(e)}", 400
    return redirect('/')
    
''' Oauth Google '''


if __name__ == '__main__':
    app.run(debug=True, port=5000)
