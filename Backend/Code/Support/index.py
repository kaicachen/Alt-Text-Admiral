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
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
csv_file = "images.csv"
annotation_complete = False

def load_dataframe():
    global df
    df = pd.read_csv(csv_file)
    df['tags_and_counts'] = df['tags_and_counts'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            subprocess.run(["python", "webscraper.py", url], check=True)
            load_dataframe()
            return redirect(url_for('annotate', index=0))
    return render_template('index.html')

@app.route('/annotate/<int:index>', methods=['GET', 'POST'])
def annotate(index):
    global annotation_complete
    if index >= len(df):
        df.to_csv(csv_file, index=False)
        annotation_complete = True
        return redirect(url_for('complete'))
    
    row = df.iloc[index]
    image_path = row['image_name']
    
    if request.method == 'POST':
        df.at[index, 'is_decorative'] = 'is_decorative' in request.form
        df.at[index, 'is_link'] = 'is_link' in request.form
        df.at[index, 'is_infographic'] = 'is_infographic' in request.form
        return redirect(url_for('annotate', index=index + 1))
    
    return render_template('annotate.html', image_path=image_path, index=index)

@app.route('/complete', methods=['GET', 'POST'])
def complete():
    if request.method == 'POST':
        subprocess.run(["python", "main_captioner.py"], check=True)
        return "Captioning process started."
    return render_template('complete.html')

if __name__ == '__main__':
    load_dataframe()
    app.run(debug=True)
