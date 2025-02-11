import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuration ---
CHROMEDRIVER_PATH = r'C:\Users\morit\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'
SEARCH_URL = "https://ygoprodeck.com/deck-search/?sort=Deck%20Views&offset=0"

# --- Setup Selenium WebDriver ---
service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
# Uncomment the next line to run headless if desired:
# options.add_argument('--headless')
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)


def accept_consent():
    """
    Click the consent button using the provided CSS selector.
    """
    try:
        consent_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                                        "body > div.fc-consent-root > div.fc-dialog-container > div.fc-dialog.fc-choice-dialog > div.fc-footer-buttons-container > div.fc-footer-buttons > button.fc-button.fc-cta-consent.fc-primary-button"
                                        ))
        )
        consent_button.click()
        print("Consent accepted.")
        time.sleep(2)  # Wait a bit for the consent to process
    except Exception as e:
        print("Consent button not found or error clicking it:", e)


try:
    # 1. Load the deck search page
    driver.get(SEARCH_URL)
    print("Loaded search page.")

    # 2. Accept the data consent popup
    accept_consent()

    # 3. Locate the first deck's link using the exact CSS path provided
    deck_selector = (
        "body > main > div > div.info-area > div.searcher-container.container-card > "
        "div.deck-searcher-bottom-pane > div.deck-layout-flex.grid-of-decks.justify-content-center.px-3.py-2 > "
        "div:nth-child(1) > div > div > div.d-flex.flex-column.text-left.p-2.rounded-bottom.deck_article-card-details.text-white > a"
    )

    deck_link = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, deck_selector))
    )

    # Optionally, print the href attribute to confirm we found the correct link.
    deck_url = deck_link.get_attribute("href")
    print("Found first deck URL:", deck_url)

    # 4. Scroll the deck element into view
    driver.execute_script("arguments[0].scrollIntoView(true);", deck_link)
    time.sleep(1)

    # 5. Instead of deck_link.click(), use JavaScript to click the element.
    driver.execute_script("arguments[0].click();", deck_link)
    print("Clicked the deck link using JavaScript.")

    # 6. Wait for the deck detail page to load.
    # Adjust the selector below if necessary – here we assume an element with class '.deck-content' indicates the deck page.
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".deck-content")))
    print("Deck detail page loaded successfully.")

except Exception as e:
    print("Error during test run:", e)

finally:
    driver.quit()
    print("Webdriver closed.")
