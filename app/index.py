'''
This will likely end up being the index.py that serves as the homepage for our Flask
implementation. Right now the entire file structure still needs to be reworked to work
with Flask, but this is the gist of the end-points for the front-end.

This file runs the webscraper, then before running main_captioner.py on the results,
it asks the user to mark whether images are decorative, links, or infographics. It then
modifies the CSV file passed to the main_captioner.py 
'''
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from sys import prefix, base_prefix, executable
from subprocess import CalledProcessError
from shutil import which as shutil_which
from os import name as os_name
from os import path, environ, urandom
import main


app = Flask(__name__)
app.secret_key = environ.get("SECRET_KEY", urandom(24))

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
        global url
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
    image_links = [data[0] for data in session.get("site_data", "none")]

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
    site_data = session.get("site_data", "none")

    # Generates alt-text for images and stores in session
    generated_data = main.process_site(site_data, tagged_list)
    session["generated_data"] = generated_data

    return redirect(url_for('displayed_images'))


# Page to show images with their alt-text
@app.route('/displayed_images', methods=['GET', 'POST'])
def displayed_images():
    # Reads data from session value
    generated_data = session.get("generated_data", "none")

    return render_template("displayed_images.html", data=generated_data)


@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"message": "Hello from Flask!", "status": "success"})


if __name__ == '__main__':
    app.run(debug=True, port=8000)
