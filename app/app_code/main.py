import os
from create_caption import *
from csv_to_pdf import create_pdf
from main_captioner import *
from web_scraper import *
import csv
import time


def run():
    url = sys.argv[1]  # url is passed to script through argv
    # site_data = scrape(url)
    # for data in site_data:
    #     create_caption(data[0],data[1])

    caption_site(url)

if __name__ == "__main__":
    run()