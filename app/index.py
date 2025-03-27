'''
This will likely end up being the index.py that serves as the homepage for our Flask
implementation. Right now the entire file structure still needs to be reworked to work
with Flask, but this is the gist of the end-points for the front-end.

This file runs the webscraper, then before running main_captioner.py on the results,
it asks the user to mark whether images are decorative, links, or infographics. It then
modifies the CSV file passed to the main_captioner.py 
'''

import pandas as pd
import ast
import subprocess
import os
import re
import sys
import shutil
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
# csv_file = "detection_results.csv"
# annotation_complete = False

# def load_dataframe():
#     global df
#     df = pd.read_csv(csv_file)
#     df['tags_and_counts'] = df['tags_and_counts'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

###########################
def get_python_path():
    """Finds the correct Python executable: prioritizes virtual environment, otherwise falls back to system Python."""
    
    # 1. Check if running inside a virtual environment
    if sys.prefix != sys.base_prefix:  
        return sys.executable  # Return the venv's Python path

    # 2. Check if a virtual environment exists in common locations
    possible_venv_dirs = [".venv", "venv", "env"]  # Add other venv folder names if your team uses different ones
    for venv_dir in possible_venv_dirs:
        python_subdir = "Scripts" if os.name == "nt" else "bin"
        venv_python = os.path.join(venv_dir, python_subdir, "python")
        if os.path.exists(venv_python):
            return venv_python  # Use the detected virtual environment Python

    # 3. If no virtual environment is found, fall back to system Python
    return shutil.which("python") or shutil.which("python3")

venv_python = get_python_path()# os.path.join(".venv", "Scripts", "python.exe")  # Adjust based on OS, for mine I have it as windows

script_path = "app/app_code/main.py"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            try:
                
                subprocess.run([venv_python, script_path, url], check=True,text=True)  # this line is causing app to crash

                # Good to move this to a separate function and web address but it's here for now for testing
                # Could mimic this format for the annotating process webpage
                output_csv = re.sub(r'[\/:*?"<>|]', '-', url)[:20]
                output_csv = output_csv + "_pool_1.csv"
                output_dict = pd.read_csv(os.path.join("app", "app_code", "outputs", "CSVs", output_csv)).to_dict(orient="records")

                return render_template("displayed_images.html", data=output_dict)

                return redirect(url_for('complete',index=0))  # On success should go to the complete page
                
            except subprocess.CalledProcessError as e:
                print(f"Error: {e}")
                print(f"Standard Output: {e.stdout}")
                print(f"Standard Error: {e.stderr}")
                return render_template('error.html')
            #load_dataframe()
    return render_template('index.html')

@app.route('/annotate/<int:index>', methods=['GET', 'POST'])
def annotate(index):
    global annotation_complete
    # if index >= len(df):
    #     df.to_csv(csv_file, index=False)
    #     annotation_complete = True
    #     return redirect(url_for('complete'))
    
    #row = df.iloc[index]
    #image_path = row['image_name']
    
    # if request.method == 'POST':
    #     df.at[index, 'is_decorative'] = 'is_decorative' in request.form
    #     df.at[index, 'is_link'] = 'is_link' in request.form
    #     df.at[index, 'is_infographic'] = 'is_infographic' in request.form
    #     return redirect(url_for('annotate', index=index + 1))
    
    #return render_template('annotate.html', image_path=image_path, index=index)

@app.route('/complete', methods=['GET', 'POST'])
def complete():
    if request.method == 'POST':
        subprocess.run(["python", "models/main_captioner.py"], check=True)
        return "Captioning process started."
    return render_template('complete.html')

if __name__ == '__main__':
    #load_dataframe()
    app.run(debug=True, port=8000)
