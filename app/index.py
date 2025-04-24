'''
This will likely end up being the index.py that serves as the homepage for our Flask
implementation. Right now the entire file structure still needs to be reworked to work
with Flask, but this is the gist of the end-points for the front-end.

This file runs the webscraper, then before running main_captioner.py on the results,
it asks the user to mark whether images are decorative, links, or infographics. It then
modifies the CSV file passed to the main_captioner.py 
'''
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, make_response
from os import name as os_name, urandom, environ, path
from authlib.integrations.flask_client import OAuth
from sys import prefix, base_prefix, executable
from subprocess import CalledProcessError
from shutil import which as shutil_which
from string import ascii_letters, digits
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from dotenv import load_dotenv
from functools import wraps
from random import choices
from . import main

# Load environmental variables
load_dotenv()

# Create Flask app
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

# Oauth Setup
app.config["SERVER_NAME"] = environ.get("SERVER_NAME")
app.config["PREFERRED_URL_SCHEME"] = environ.get("URL_SCHEME")
oauth = OAuth(app)


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


'''Blocks caching for user authenticated pages'''
def nocache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return no_cache_view


'''Main home page'''
@app.route('/', methods=['GET', 'POST'])
def index():
    # Clear all session data besides user ID
    user_id = session.get("user_id", None)
    session.clear()
    session["user_id"] = user_id

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
                
            # Remain on home page if URL is invalid
            except ValueError as e:
                print(f"Error: {e}")
    
    return render_template('index.html')


'''Route for Chrome extension to connect to'''
@app.route('/extension',methods=['POST','GET'])
def test():
    data = request.get_json()
    url = data["url"]  # it's like this because data is a json that I get the url from

    # This should work now ?
    validated_url, site_data = main.web_scraper(url)
    session["url"] = validated_url
    session["site_data"] = site_data

    return jsonify({"redirect_url": url_for("annotate")})


'''Page to allow for user annotations of images'''
@app.route('/annotate', methods=['GET', 'POST'])
@nocache
def annotate():
    # Reads scraped data from session values
    site_data = session.get("site_data", None)

    if site_data is None:
        print("Invalid access to /annotate, redirecting home")
        return redirect(url_for('index'))
    
    # Gets image links from site data
    image_links = [data[0] for data in site_data]

    image_tags = []

    # Default to "don't include" tag if invalid URL
    for image in image_links:
        if image == "true":
            image_tags.append(3)
        else:
            image_tags.append(0)
    # Pass 'no_images_found' flag to template
    no_images_found = len(image_links) == 0

    return render_template("annotate.html", image_links=image_links, image_tags=image_tags, no_images_found=no_images_found)


'''JSON to process annotations from user'''
@app.route('/process_images', methods=['GET', 'POST'])
def process_images():
    # Gets the JSON storing the user's image annotations
    data = request.get_json()
    tagged_list = data.get("taggedList", None)
    added_image_list = data.get("addedImageList", None)

    if tagged_list is None:
        print("Invalid access to /process_images, redirecting home")
        return redirect(url_for('index'))

    # Reads data from session values
    site_data = session.get("site_data", None)
    url       = session.get("url", None)
    user_id   = session.get("user_id", None)

    # Add images extra images to site data
    site_data.extend([(None, "", "", main.reduce_image_size(image)) for image in added_image_list])

    # Generates alt-text for images and stores in session
    generated_data, generation_id, data_ids = main.process_site(site_data, tagged_list, url, user_id)
    session["generated_data"] = generated_data
    session["generation_id"]  = generation_id
    session["data_ids"]       = data_ids
    session["tagged_list"]    = tagged_list
    session["site_data"]      = site_data

    return redirect(url_for('displayed_images'))


'''Page to show images with their alt-text'''
@app.route('/displayed_images', methods=['GET', 'POST'])
@nocache
def displayed_images():
    # Reads data from session value
    generated_data = session.get("generated_data", None)
    data_ids       = session.get("data_ids", None)

    if generated_data is None:
        print("Invalid access to /displayed_images, redirecting home")
        return redirect(url_for('index'))

    return render_template("displayed_images.html", data=generated_data, data_ids=data_ids)


'''End point to check for valid URL'''
@app.route('/check_url')
def check_url():
    newURL = request.args.get('url') 
    try:
        response = requests.head(newURL, timeout=3)
        return jsonify({'valid': response.status_code < 400})
    except:
        return jsonify({'valid':False})
    

'''End point to regenerate an image's alt-text'''
@app.route('/regenerate_image', methods=['GET', 'POST'])
def regenerate_image():
    # Gets the JSON storing the index of the data
    data = request.get_json()
    data_index = int(data.get("data_index", 0)) - 1

    if data_index == -1:
        print("Invalid access to /regenerate_image, redirecting home")
        return redirect(url_for('index'))

    generated_data = session.get("generated_data", None)
    site_data      = session.get("site_data", None)
    data_ids       = session.get("data_ids", None)
    tagged_list    = session.get("tagged_list", None)

    if site_data is None:
        print("Invalid access to /regenerate_image, redirecting home")
        return redirect(url_for('index'))

    print(f"Regenerating image {data_index}")

    # User uploaded image
    if site_data[data_index][0] is None:
        # Generate new alt text with the stored data
        alt_text = main.regenerate(data_ids[data_index],
                                tagged_list[data_index],
                                site_data[data_index][3],
                                site_data[data_index][1],
                                site_data[data_index][2])
        
        # Updates the data tuple
        generated_data[data_index] = (site_data[data_index][3],
                                    alt_text)
        
    # Standard scraped image
    else:
        # Generate new alt text with the stored data
        alt_text = main.regenerate(data_ids[data_index],
                                tagged_list[data_index],
                                site_data[data_index][0],
                                site_data[data_index][1],
                                site_data[data_index][2])
    
        # Updates the data tuple
        generated_data[data_index] = (site_data[data_index][0],
                                    alt_text)

    # Update stored data
    session["generated_data"] = generated_data

    # Reload images
    return redirect(url_for('displayed_images'))
    

'''Page to display previous generation history'''
@app.route('/history')
@nocache
def history():
    user_id = session.get("user_id", None)

    if user_id is None:
        print("Invalid access to /history, redirecting home")
        return redirect(url_for('index'))

    history = main.load_history(user_id)
    return render_template('history.html', history_data=history)


'''Endpoint to process previous generation'''
@app.route('/process_previous_results', methods=['GET', 'POST'])
def process_previous_results():
    # Gets the JSON storing the generation ID
    data = request.get_json()
    generation_id = int(data.get("generation_id", -1))

    if generation_id == -1:
        print("Invalid access to /process_previous_results, redirecting home")
        return redirect(url_for('index'))

    generated_data, data_ids = main.load_generation(generation_id)

    session["generated_data"] = generated_data
    session["generation_id"]  = generation_id
    session["data_ids"]       = data_ids

    return redirect(url_for('previous_results'))


'''Page to display previous generation'''
@app.route('/previous_results', methods=['GET', 'POST'])
@nocache
def previous_results():
    # Reads data from session value
    generated_data = session.get("generated_data", None)
    data_ids       = session.get("data_ids", None)

    if generated_data is None:
        print("Invalid access to /displayed_images, redirecting home")
        return redirect(url_for('index'))

    return render_template("previous_results.html", data=generated_data, data_ids=data_ids)
    

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"message": "Hello from Flask!", "status": "success"})


# @app.route("/proxy")
# def proxy():
#     try:
#         response = requests.get(url, timeout=5)
#         content_type = response.headers.get('Content-Type', 'text/html')
#         return Response(response.content, content_type=content_type)
#     except Exception as e:
#         print(f"Proxy error: {e}")
#         return Response(f"Error fetching URL: {e}", status=500)


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
        user_info = oauth.google.parse_id_token(token, nonce=nonce)

        email = user_info.get("email")
        if not email:
            return "Email not found in user info", 400
        # Database stuff should go around here
        user_id = main.login_user(email=email)
        session['user_id'] = user_id
        session['user_email'] = email

        return """
        <html><body>
        <script>
            window.opener.postMessage({ type: 'oauth_success' }, '*');
            window.close();
        </script>
        <p>Login successful. You can close this window.</p>
        </body></html>
        """

    except Exception as e:
        return f"Error while parsing ID token: {str(e)}", 400
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
