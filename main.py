import os
import time
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuration ---
CHROMEDRIVER_PATH = r'C:\Users\morit\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'
BASE_URL = "https://ygoprodeck.com/deck-search/?sort=Deck%20Views&offset={offset}"
START_OFFSET = 0  # starting offset (0 for the first page)
NUM_PAGES = 3  # number of pages to process; adjust as needed

# --- Setup Selenium WebDriver ---
service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
# Uncomment the following line to run in headless mode:
# options.add_argument('--headless')
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)


def accept_consent():
    """
    Clicks the data consent popup using the provided CSS selector.
    Returns True if the consent button was successfully clicked.
    """
    accepted = False
    try:
        consent_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                                        "body > div.fc-consent-root > div.fc-dialog-container > div.fc-dialog.fc-choice-dialog > div.fc-footer-buttons-container > div.fc-footer-buttons > button.fc-button.fc-cta-consent.fc-primary-button"
                                        ))
        )
        consent_button.click()
        print("Consent button clicked.")
        accepted = True
        time.sleep(2)  # Allow time for the consent action to complete
    except Exception as e:
        print("Error clicking consent button:", e)
    return accepted


try:
    # Loop through the deck search pages
    for page in range(NUM_PAGES):
        current_offset = START_OFFSET + page * 20
        search_url = BASE_URL.format(offset=current_offset)
        print(f"\nLoading deck search page: {search_url}")
        driver.get(search_url)

        # Accept the data consent popup
        accept_consent()

        # --- Extract deck links from the search page ---
        try:
            deck_link_elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.deck-card-link"))
            )
        except Exception as e:
            print("Error finding deck links:", e)
            continue

        deck_urls = [elem.get_attribute("href") for elem in deck_link_elements if elem.get_attribute("href")]
        print(f"Found {len(deck_urls)} decks on this page.")

        # Process each deck URL
        for deck_url in deck_urls:
            print(f"\nProcessing deck: {deck_url}")
            try:
                driver.get(deck_url)

                # Wait for the deck detail page to load (adjust the selector if needed)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".deck-content")))

                # --- Click on the "More..." button to reveal the download option ---
                try:
                    more_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'More')]"))
                    )
                    more_button.click()
                    print("Clicked 'More...' button.")
                    time.sleep(1)
                except Exception as e:
                    print("Could not find or click the 'More...' button:", e)
                    continue

                # --- Locate the Download YDK button/link ---
                try:
                    download_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Download YDK')]"))
                    )
                    ydk_url = download_button.get_attribute("href")
                    if not ydk_url:
                        print("Download URL not found.")
                        continue
                    print("Found YDK URL:", ydk_url)
                except Exception as e:
                    print("Could not locate the Download YDK button:", e)
                    continue

                # --- Download the YDK file ---
                try:
                    response = requests.get(ydk_url)
                    response.raise_for_status()
                    # Use the basename from the URL or another naming convention
                    filename = os.path.basename(ydk_url) or "deck.ydk"
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    print(f"Downloaded deck as {filename}")
                except Exception as e:
                    print("Failed to download YDK file:", e)

            except Exception as deck_exception:
                print(f"Error processing deck at {deck_url}:", deck_exception)

            # Pause between deck downloads to be polite to the server.
            time.sleep(1)

finally:
    driver.quit()
    print("Webdriver closed.")
