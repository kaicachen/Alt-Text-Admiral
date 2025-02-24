# Machine Generated Alt-Text
Machine generated alt-text for websites

## TO INSTALL VIRTUAL ENVIRONMENT:
- sudo apt install python3-venv if you don't already have it

- To create environment:
    - python3 -m venv venv

- To run environment:
    - source venv/bin/activate
    - For Windows: cd to venv/Scripts, then type ./activate

- To exit environment:
    - deactivate

### TO INSTALL PACKAGES:
- First be in your virtual environmet, then run
    - pip install -r requirements.txt

## TO GENERATE ALT-TEXT FOR IMAGES SCRAPED FROM WEBPAGE:
- Provide website URL to main_captioner.py
- Run main_captioner.py
- Outputs:
    - outputs.csv containing image_filepath,generated_alt-text pairs
    - outputs.pdf containing nicely formatted images next to alt-text

## TO GENERATE ALT-TEXT USING TEST IMAGES:
- Ensure images are in "images" directory
- Run test_script.py
- Outputs:
    - test_outputs.csv containing image_filepath,generated_alt-text pairs
    - test_outputs.pdf containing nicely formatted images next to alt-text

## TO RUN JUST THE WEB SCRAPER:
- Provide website URL to web_scraper.py
- Run web_scraper.py
- Output:
    - Console output containing images and surrounding text found on webpage

## *ONCE FRONT END OPERATIONAL* (ESTIMATED FOR SPRINT THREE):
### TO USE PROGRAM:
- Navigate to [SITE_URL]
- Input URL of webpage you wish to generate alt-text for images on
- Click "Start Generation" button
- Output:
    - 