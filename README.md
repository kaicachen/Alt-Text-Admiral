# Alt-Text Admiral

Source code for website to create ADA compliant alt-text using AI models, specifically Gemini 1.5 Flash and Facebook's DETR-ResNet-50.

## Description

This project is a Flask app connected to Supabase using OAuth to allow for users to enter in their website URL and get the alt text for all of the images used in that site. This will allow for more website owners to add this important accessibilty feature to their sites. To use the site, a user would navigate to the hosting site where they either login if they want their generations saved, or continue as guest. Then they would enter a URL into the central search bar and click the button to start the process. Next, they would tag the images as informative, decorative, links, or do not include, as these are the categories for alt-text. Then the process starts, and a user can either leave the site and come back later to view the saved generations, or stay and view them once all have been processed.

## Getting Started
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
Create a new virtual environment for the server
- `python3 -m venv venv`
- Alternatively `python -m venv /path/to/new/virtual/environment`
Ensure the virtual environment is activated
- `source venv/bin/activate`
- For Windows: `cd venv/Scripts`, then type `./activate`
To exit environment when not running server:
    - `deactivate`

### TO INSTALL NECCESSARY PACKAGES:
First, be in your virtual environmet, then run
- `pip install -r requirements.txt`


## WEBSITE OPERATION
Once all the dependencies have been met, the server can be started by running the following command in the source folder with the virtual environment activated.
- `python -m app.index`

# Backend Usage
We do not recommend using the website from individual scripts.



## Authors

- [Aiden Patel](https://github.com/aidenap21)
- [Andrew McFerrin](https://github.com/AMcFerrin)
- [Landon Pyko](https://github.com/LandonPyko)
- [Kai Achen](https://github.com/kaicachen)
- [John Newman](https://github.com/JohnDNewman)

## License

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details