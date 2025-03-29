from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import csv
import sys
import re
import os

def scrape(url):  # URL -> List of scraped data
    # Set up Selenium WebDriver
    print("THIS IS RUNNING")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run without opening browser

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)  # Change to your target site

    time.sleep(3)  # Allow JavaScript to load content

    image_text_data = []
    
    # Find all standard images
    images = driver.find_elements(By.XPATH, "//img[not(ancestor::comment())]")
    for img in images:
        try:
            #If data-lazyload exists then use that as source? else use src?
            #img_url = img.get_attribute("src")
            img_url = img.get_attribute("data-lazyload") or img.get_attribute("data-src") or img.get_attribute("src")
            alt_text = img.get_attribute("alt") or ""  # Extract alt text

            # Clean img_url
            if img_url[:2] == '//':
                print(f"Changing {img_url}")
                img_url = 'https:' + img_url

            # Get text from the closest paragraph (<p>), div, or span before & after the image
            prev_text = ""
            next_text = ""

            try:
                prev_text = img.find_element(By.XPATH, "preceding::p[1] | preceding::div[1] | preceding::span[1]").text.strip()
            except:
                pass

            try:
                next_text = img.find_element(By.XPATH, "following::p[1] | following::div[1] | following::span[1]").text.strip()
            except:
                pass

            # Get text from multiple levels of parent elements
            parent_text = ""
            parent = img
            for _ in range(3):  # Check up to 3 levels up
                try:
                    parent = parent.find_element(By.XPATH, "..")
                    parent_text = parent.text.strip()
                    if parent_text:
                        break  # Stop if we find valid text
                except:
                    break

            # Combine all text sources
            surrounding_text = " ".join(filter(None, [alt_text, prev_text, parent_text, next_text]))
            image_text_data.append((img_url, surrounding_text))

        except Exception as e:
            print(f"Error processing image: {e}")
    
    # Find Revolution Slider images (which use divs with background images)
    rev_slider_divs = driver.find_elements(By.XPATH, "//div[contains(@class, 'rev_slider') or contains(@class, 'tp-bgimg')]")
    for div in rev_slider_divs:
        try:
            style = div.get_attribute("style")
            match = re.search(r'url\((.*?)\)', style)
            if match:
                img_url = match.group(1).strip('"')
                
                # Get text from surrounding elements
                parent_text = ""
                parent = div
                for _ in range(3):  # Check up to 3 levels up
                    try:
                        parent = parent.find_element(By.XPATH, "..")
                        parent_text = parent.text.strip()
                        if parent_text:
                            break  # Stop if we find valid text
                    except:
                        break
                
                image_text_data.append((img_url, parent_text))
        
        except Exception as e:
            print(f"Error processing Revolution Slider image: {e}")
    
    driver.quit()

    # Create CSV output of scraped tuples
    output_name = re.sub(r'[\/:*?"<>|]', '-', url)[:20]
    with open(os.path.join("app", "app_code", "outputs", "CSVs", "Site Data", f"RAW_TUPLES_{output_name}.csv"), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        
        # Write a header row (optional)
        writer.writerow(["image_link", "surrounding_text"])
        
        for image, text in image_text_data:
            writer.writerow([
                image,
                text
            ])

    return image_text_data

if __name__ == "__main__":
    url = sys.argv[1]  # url is passed to script through argv
    site_data = scrape(url)
