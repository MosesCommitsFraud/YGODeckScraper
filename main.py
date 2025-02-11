import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- Configuration ---
CHROMEDRIVER_PATH = r'C:\Users\morit\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'
SEARCH_URL = "https://ygoprodeck.com/deck-search/?sort=Deck%20Views&offset=0"
DECK_URL = "https://ygoprodeck.com/deck/blue-eyes-meta-deck-2020-new-rules-69017"

# --- Setup Selenium WebDriver ---
print("Setting up the WebDriver...")
service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
# Uncomment the following line to run headless:
# options.add_argument('--headless')
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)  # increased timeout to 20 seconds

def accept_consent():
    """
    Accepts the consent popup using the provided CSS selector.
    """
    try:
        print("Waiting for consent popup...")
        consent_button = wait.until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "body > div.fc-consent-root > div.fc-dialog-container > div.fc-dialog.fc-choice-dialog > div.fc-footer-buttons-container > div.fc-footer-buttons > button.fc-button.fc-cta-consent.fc-primary-button"
            ))
        )
        consent_button.click()
        print("Consent accepted.")
        time.sleep(2)  # Allow time for the consent to process
    except Exception as e:
        print("Consent button not found or error clicking it:", e)

try:
    # 1. Load the deck search page (this triggers the consent popup).
    print("Loading the search page...")
    driver.get(SEARCH_URL)
    print("Search page loaded.")
    accept_consent()
    time.sleep(1)

    # 2. Navigate to the deck detail page.
    print("Navigating to the deck detail page...")
    driver.get(DECK_URL)
    # Wait for the main deck element to be present.
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#main_deck")))
    print("Deck detail page loaded.")

    # 3. Retrieve and parse the page source.
    print("Retrieving page source...")
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    print("Page source parsed.")

    # 4. Locate the deck sections using their IDs.
    print("Locating deck sections...")
    main_section  = soup.select_one("#main_deck")
    extra_section = soup.select_one("#extra_deck")
    side_section  = soup.select_one("#side_deck")

    if main_section is None:
        print("Could not find the main deck container (#main_deck).")
    else:
        print("Main deck container found.")
    if extra_section is None:
        print("Could not find the extra deck container (#extra_deck).")
    else:
        print("Extra deck container found.")
    if side_section is None:
        print("Could not find the side deck container (#side_deck).")
    else:
        print("Side deck container found.")

    # 5. Extract card IDs from each section.
    # Each card is represented by an <img> tag with classes "lazy master-duel-card"
    # and the card ID is stored in its "data-name" attribute.
    def extract_card_ids(section):
        if section is None:
            return []
        images = section.find_all("img", class_="lazy master-duel-card")
        print(f"Found {len(images)} card images in section.")
        return [img.get("data-name") for img in images if img.has_attr("data-name")]

    print("Extracting main deck card IDs...")
    main_cards  = extract_card_ids(main_section)
    print("Extracting extra deck card IDs...")
    extra_cards = extract_card_ids(extra_section)
    print("Extracting side deck card IDs...")
    side_cards  = extract_card_ids(side_section)

    # 6. Build the YDK file content.
    print("Building YDK content...")
    ydk_lines = []
    ydk_lines.append("#main")
    ydk_lines.extend(main_cards)
    ydk_lines.append("#extra")
    ydk_lines.extend(extra_cards)
    ydk_lines.append("!side")
    ydk_lines.extend(side_cards)
    ydk_content = "\n".join(ydk_lines) + "\n"

    # 7. Save the content to a file.
    output_filename = "deck.ydk"
    with open(output_filename, "w") as f:
        f.write(ydk_content)
    print(f"Deck YDK file created successfully as '{output_filename}'!")

except Exception as e:
    print("Error during run:", e)

finally:
    driver.quit()
    print("Webdriver closed.")
