# Alt-Text Admiral

Source code for website to create ADA compliant alt-text using AI models, specifically Gemini 1.5 Flash and Facebook's DETR-ResNet-50.

## Project Demonstration Video
[![Alt-Text Admiral Demo](https://img.youtube.com/vi/e6N2HrlnfZA/0.jpg)](https://www.youtube.com/watch?v=e6N2HrlnfZA)

## Description

This application allows users to enter in their website URL and generate alt text for all of the images used in that site. This will enable website administrators to quickly and easily add this important accessibilty feature to their sites. To use the site, a user may either login if they want their generations saved, or continue as guest. Then they would enter a URL to the form and click the "Start Scraping" button to start the process. Next, they would tag the images as informative, decorative, links, or do not include, as these are common categories for alt-text. Once the user has finished tagging images, the generation process begins, and a user can either leave the site and come back later to view the saved generations, or stay and view them once all have been processed. If users do not find the resulting generation satisfactory, they can easily regenerate for individual offending images.

### TECHNOLOGY USED:
- Flask web framework (Python, HTML, CSS, JavaScript)
- Supabase (PostGreSQL)
- Gemini 1.5 Flash (Python)
- DETR-ResNet-50 (Python)
- Git, Github (Version Control)

## AUTHORS:

- [Aiden Patel](https://github.com/aidenap21)
- [Andrew McFerrin](https://github.com/AMcFerrin)
- [Landon Pyko](https://github.com/LandonPyko)
- [Kai Achen](https://github.com/kaicachen)
- [John Newman](https://github.com/JohnDNewman)

## GETTING STARTED:
The server requires
- A python virtual environment with required packages installed
- A chrome installation on the machine
- The following variables in a .env file in the source folder
    - GEMINI_API_KEY=\*An API key for accessing Google Gemini*
    - SUPABASE_URL=\*A Project URL for Supabase*
    - SUPABASE_API_KEY=\*An API key for Supabase*
    - SUPABASE_DB_URL=\*A Direct Connection PostgreSQL URL for Supabase*
    - SERVER_NAME=\*Name of where the server is hosted*
    - URL_SCHEME=\*The URL scheme of where the server is hosted*
    - GOOGLE_CLIENT_ID=\*Your client ID for Google OAuth*
    - GOOGLE_CLIENT_SECRET=\*Your client secret for Google OAuth*
    - EMAIL_ADDRESS=\*Email address to send emails with*
    - EMAIL_PASSWORD=\*Password to above email*

### TO INSTALL VIRTUAL ENVIRONMENT:
Install python venv if you don't already have it
- `sudo apt install python3-venv`
- Create a new virtual environment for the server
- `python3 -m venv venv`
- Alternatively `python -m venv /path/to/new/virtual/environment`
- Ensure the virtual environment is activated
- `source venv/bin/activate`
- For Windows: `cd venv/Scripts`, then type `./activate`
- To exit environment when not running server: `./deactivate`

### TO INSTALL NECCESSARY PACKAGES:
Within virtual environment and base folder, run
- `pip install -r requirements.txt`

## WEBSITE OPERATION:
Once all the dependencies have been met, the server can be started by running the following command in the source folder with the virtual environment activated.
- `python -m app.index`
Currently this app will run on localhost:5000. We explored several options for deployment, but none of them worked out in time due to a combination of price and resource issues.
Users may then use the app by navigating to localhost:5000 on their browser of choice and using the intuitive UI.

### FEATURES:
- Users can create accounts by logging in with their Google accounts using OAuth2.0.
    - This saves any websites the user has scraped and generated alt-text for in our Supabase database.
    - Users can then go back and look at the 10 most recent generations.
- Web scraping to detect images on webpages without the need for users to manually input images.
    - Users can also manually add images as they wish.
- Machine learning powered alt-text generation based on image contents and surrounding contextual information on the page.
- Easy regeneration for individual images.
- Three convenient file formats for downloading the generation results (CSV, JSON, HTML).