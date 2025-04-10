'''
This will likely end up being the index.py that serves as the homepage for our Flask
implementation. Right now the entire file structure still needs to be reworked to work
with Flask, but this is the gist of the end-points for the front-end.

This file runs the webscraper, then before running main_captioner.py on the results,
it asks the user to mark whether images are decorative, links, or infographics. It then
modifies the CSV file passed to the main_captioner.py 
'''
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
from sys import prefix, base_prefix, executable
from subprocess import run, CalledProcessError
from shutil import which as shutil_which
from json import dumps as json_dumps
from os import name as os_name
from pandas import read_csv
from csv import reader
from os import path
from re import sub


app = Flask(__name__)
CORS(app)

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
                run([python_path, "app/app_code/web_scraper.py", url, False], check=True,text=True)
                return redirect(url_for('annotate'))
                
            except CalledProcessError as e:
                print(f"Error: {e}")
                print(f"Standard Output: {e.stdout}")
                print(f"Standard Error: {e.stderr}")
                return render_template('error.html')
    
    return render_template('index.html')

@app.route('/extension',methods=['POST','GET'])
def test():
    data = request.get_json()
    global url
    url = data["url"]
    run([python_path, "app/app_code/web_scraper.py", url, "True"], check=True,text=True)
    

    return redirect(url_for('annotate'))


    

'''Page to allow for user annotations of images'''
@app.route('/annotate', methods=['GET', 'POST'])
def annotate():
    # Reads scraped data from CSV output
    image_links = []
    image_tags = []
    filename = sub(r'[\/:*?"<>|]', '-', url)[:20]
    
    with open(path.join("app", "app_code", "outputs", "CSVs", "Site Data", f"RAW_TUPLES_{filename}.csv"), mode="r", newline="", encoding="utf-8") as file:
        csv_reader = reader(file)
        
        # Read a header row
        next(csv_reader)
        
        for row in csv_reader:  # NOT WORKING HERE. CHECK BACK LATER
            print("RUNNING!!!\n")
            if row[0] == 'true':
                image_tag = 3
            else:
                image_tag = 0
            
            image_links.append(row[0])
            image_tags.append(image_tag)
    
    return render_template("annotate.html", image_links=image_links, image_tags=image_tags)


'''JSON to process annotations from user'''
@app.route('/process_images', methods=['GET', 'POST'])
def process_images():
    # Gets the JSON storing the user's image annotations
    data = request.get_json()
    tagged_list = data.get("taggedList", [])

    # Generates alt-text for images
    run([python_path, "app/app_code/site_processor.py", url, json_dumps(tagged_list)], check=True, text=True)  # this line is causing app to crash
    return redirect(url_for('displayed_images'))


# Page to show images with their alt-text
@app.route('/displayed_images', methods=['GET', 'POST'])
def displayed_images():
    # Reads images and corresponding generated alt-text from CSV output
    output_csv = sub(r'[\/:*?"<>|]', '-', url)[:20] + ".csv"
    output_dict = read_csv(path.join("app", "app_code", "outputs", "CSVs", output_csv)).to_dict(orient="records")

    return render_template("displayed_images.html", data=output_dict)


@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"message": "Hello from Flask!", "status": "success"})


if __name__ == '__main__':
    app.run(debug=True, port=8000)
