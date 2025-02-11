import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- Configuration ---
CHROMEDRIVER_PATH = r'C:\Users\morit\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'
SEARCH_URL = "https://ygoprodeck.com/deck-search/?sort=Deck%20Views&offset=0"
# (No static deck URL needed since we'll click decks on the search page)

# --- Setup Selenium WebDriver ---
print("Setting up the WebDriver...")
service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
# Uncomment to run headless:
# options.add_argument('--headless')
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)  # increased timeout


def accept_consent():
    """
    Accept the consent popup using its CSS selector.
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
        time.sleep(2)  # Give time for the consent to process
    except Exception as e:
        print("Consent button not found or error clicking it:", e)


def extract_card_ids(section):
    """
    Given a BeautifulSoup element representing a deck section,
    finds all <img> tags with class "lazy master-duel-card" and
    returns a list of card IDs extracted from their data-name attribute.
    """
    if section is None:
        return []
    images = section.find_all("img", class_="lazy master-duel-card")
    print(f"  Found {len(images)} card images in section.")
    return [img.get("data-name") for img in images if img.has_attr("data-name")]


try:
    # 1. Load the deck search page and accept consent.
    print("Loading the search page...")
    driver.get(SEARCH_URL)
    time.sleep(2)  # Allow time for the page to load
    accept_consent()
    time.sleep(2)

    # 2. Extract deck links from the search page.
    # The clickable deck link has the class:
    # "stretched-link text-decoration-none text-reset text-truncate deck_article-card-title"
    deck_elements = driver.find_elements(By.CSS_SELECTOR,
                                         "a.stretched-link.text-decoration-none.text-reset.text-truncate.deck_article-card-title"
                                         )
    print(f"Found {len(deck_elements)} deck elements on the search page.")

    # To avoid stale elements after navigation, extract (href, deck name) pairs.
    deck_list = []
    for elem in deck_elements:
        href = elem.get_attribute("href")
        name = elem.text.strip()
        deck_list.append((href, name))

    print("Extracted deck list from search page.")

    # Store the original window handle (the search page).
    original_window = driver.current_window_handle

    # 3. Iterate over each deck.
    for idx, (deck_url, deck_name) in enumerate(deck_list, start=1):
        print(f"\nProcessing deck {idx}: '{deck_name}' ({deck_url})")

        # Open the deck detail page in a new tab.
        driver.execute_script("window.open(arguments[0], '_blank');", deck_url)
        time.sleep(2)
        # Switch to the newly opened tab (assume it's the last window).
        windows = driver.window_handles
        driver.switch_to.window(windows[-1])

        try:
            # 4. Wait for the deck detail page to load by waiting for #main_deck.
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#main_deck")))
            print("Deck detail page loaded.")

            # 5. Retrieve and parse the deck detail page HTML.
            deck_html = driver.page_source
            deck_soup = BeautifulSoup(deck_html, "html.parser")

            # (Optionally, re-read the deck name from the deck detail page if needed.)
            # For now, we'll use the name we extracted from the search page.

            # 6. Locate the three deck sections.
            main_section = deck_soup.select_one("#main_deck")
            extra_section = deck_soup.select_one("#extra_deck")
            side_section = deck_soup.select_one("#side_deck")

            if main_section is None:
                print("  Warning: Could not find the main deck container (#main_deck).")
            if extra_section is None:
                print("  Warning: Could not find the extra deck container (#extra_deck).")
            if side_section is None:
                print("  Warning: Could not find the side deck container (#side_deck).")

            # 7. Extract card IDs from each section.
            print("Extracting main deck card IDs...")
            main_cards = extract_card_ids(main_section)
            print("Extracting extra deck card IDs...")
            extra_cards = extract_card_ids(extra_section)
            print("Extracting side deck card IDs...")
            side_cards = extract_card_ids(side_section)

            # 8. Build the YDK file content.
            ydk_lines = []
            ydk_lines.append("#main")
            ydk_lines.extend(main_cards)
            ydk_lines.append("#extra")
            ydk_lines.extend(extra_cards)
            ydk_lines.append("!side")
            ydk_lines.extend(side_cards)
            ydk_content = "\n".join(ydk_lines) + "\n"

            # 9. Sanitize the deck name to create a safe filename.
            safe_deck_name = re.sub(r'[^A-Za-z0-9_\-]', '_', deck_name)
            filename = safe_deck_name + ".ydk"

            # 10. Save the YDK content to a file.
            with open(filename, "w", encoding="utf-8") as f:
                f.write(ydk_content)
            print(f"Created YDK file: '{filename}'")

        except Exception as e:
            print("Error processing deck detail page:", e)
        finally:
            # Close the current tab and switch back to the search page tab.
            driver.close()
            driver.switch_to.window(original_window)
            time.sleep(2)

except Exception as e:
    print("Error during run:", e)

finally:
    driver.quit()
    print("Webdriver closed.")
