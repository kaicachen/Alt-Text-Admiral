from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from requests import get
from time import sleep
from io import BytesIO
from PIL import Image
from re import search
from sys import argv

'''Class to perform webscraping of image and text tuples'''
class WebScraper:
    def __init__(self, url:str):
        self.site_url = url

    '''Tests connection to URL'''
    def _test_url(self, url:str) -> bool:
        try:
            response = get(url, timeout=5)
            response.raise_for_status()
            return True
        
        except:
            return False

    '''Tests connection to URL and sanitizes if needed'''
    def _validate_url(self)->str:
        # Ensure reachable URL and early exit if not
        if self._test_url(self.site_url):
            return self.site_url
        
        # Case of 'www.example.com'
        if self.site_url[:4] == "www.":
            cleaned_url = "https://" + self.site_url
            if self._test_url(cleaned_url):
                return cleaned_url
            
            cleaned_url = "http://" + url
            if self._test_url(cleaned_url):
                return cleaned_url
            
            else:
                raise ValueError("Failed to sanitize URL and connect")
        
        # Case of 'example.com'
        else:
            cleaned_url = "https://www." + self.site_url
            if self._test_url(cleaned_url):
                return cleaned_url
            
            cleaned_url = "http://www." + self.site_url
            if self._test_url(cleaned_url):
                return cleaned_url
            
            else:
                raise ValueError("Failed to sanitize URL and connect")


    '''Filter out placeholder images or single color images'''
    def _filter_images(self, image_text_data:list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
        validated_data = []
        for image_url, text, href, in image_text_data:
            try:
                response = get(image_url)
                image = Image.open(BytesIO(response.content))

            except:
                print(f"ERROR LOADING IMAGE {image_url}, REMOVING")
                continue

            # Finds all colors in an image
            colors = image.getcolors(image.size[0] * image.size[1])

            # Removes single pixel images or single color images
            if (image.width == 1 and image.height == 1) or len(colors) == 1:
                continue

            validated_data.append((image_url, text, href))

        return validated_data


    '''Scrapes a given URL to create tuples of images and surrounding text'''
    def scrape_site(self)-> tuple[str, list[tuple[str, str, str]]]:
        # Validates URL
        validated_url = self._validate_url()

        # Set up Selenium WebDriver
        options = webdriver.ChromeOptions()

        # Run without opening a browser
        options.add_argument("--headless")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(validated_url)

        # Allow JavaScript to load content
        sleep(3)

        # Initializes empty list to store image, text tuples
        image_text_data:list[tuple[str, str, str]] = []
        
        # Find all standard images
        images = driver.find_elements(By.XPATH, "//img[not(ancestor::comment())]")
        for img in images:
            try:
                # If data-lazyload exists then use that as source, else use src
                img_url = img.get_attribute("data-lazyload") or img.get_attribute("data-src") or img.get_attribute("src")

                # Extract alt-text
                alt_text = img.get_attribute("alt") or ""

                # Try to find a parent anchor tag and get its href
                href = ""
                try:
                    anchor = img.find_element(By.XPATH, "ancestor::a[1]")
                    href = anchor.get_attribute("href") or ""
                except:
                    pass

                # Clean img_url
                if img_url[:2] == '//':
                    print(f"Changing {img_url}")
                    img_url = 'https:' + img_url

                # Clean href
                if href[:2] == '//':
                    print(f"Changing {href}")
                    href = 'https:' + href

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

                        # Stop if valid text is found
                        if parent_text:
                            break

                    except:
                        break

                # Combine all text sources
                surrounding_text = " ".join(filter(None, [alt_text, prev_text, parent_text, next_text]))
                image_text_data.append((img_url, surrounding_text, href))

            except Exception as e:
                print(f"Error processing image: {e}")
        
        # Find Revolution Slider images (which use divs with background images)
        rev_slider_divs = driver.find_elements(By.XPATH, "//div[contains(@class, 'rev_slider') or contains(@class, 'tp-bgimg')]")
        for div in rev_slider_divs:
            try:
                style = div.get_attribute("style")
                match = search(r'url\((.*?)\)', style)
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
                    
                    image_text_data.append((img_url, parent_text, ""))
            
            except Exception as e:
                print(f"Error processing Revolution Slider image: {e}")
        
        driver.quit()

        validated_data = self._filter_images(image_text_data)

        # Returns validated URL and image, text tuple list
        return validated_url, validated_data


if __name__ == "__main__":
    # URL is passed to script through argv
    url = argv[1]
    web_scraper = WebScraper(url)
    validated_url, site_data = web_scraper.scrape_site()
