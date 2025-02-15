import time
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- Configuration ---
CHROMEDRIVER_PATH = r'C:\Users\morit\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'
# Use the first page URL (offset parameter is not used for pagination anymore)
BASE_SEARCH_URL = "https://ygoprodeck.com/category/format/tournament%20meta%20decks?offset=1000"

# Folder to save the downloaded YDK files.
download_folder = "ydk_download"
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

# --- Setup Selenium WebDriver ---
print("Setting up the WebDriver...")
service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
# Uncomment the next line to run headless:
# options.add_argument('--headless')
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)  # increased timeout

def accept_consent():
    """
    Accepts the consent popup using its CSS selector.
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
        time.sleep(2)
    except Exception as e:
        print("Consent popup not found or error:", e)

def extract_card_ids(section):
    """
    Given a BeautifulSoup element representing a deck section,
    finds all <img> tags with class "lazy master-duel-card" and returns
    a list of card IDs from their data-name attribute.
    """
    if section is None:
        return []
    images = section.find_all("img", class_="lazy master-duel-card")
    print(f"  Found {len(images)} card images in section.")
    return [img.get("data-name") for img in images if img.has_attr("data-name")]

try:
    # 1. Load the first search page and accept consent.
    print("Loading initial search page...")
    driver.get(BASE_SEARCH_URL)
    time.sleep(2)
    accept_consent()
    time.sleep(2)

    while True:
        # Wait for the deck container to be present.
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#latest-decks")))
        except Exception as e:
            print("Timeout waiting for deck container:", e)
            break

        # Extra wait to ensure all decks are loaded.
        time.sleep(5)

        # Parse the current page HTML.
        search_html = driver.page_source
        search_soup = BeautifulSoup(search_html, "html.parser")

        # Extract all deck links.
        # (Using a selector similar to the one you provided but without nth-child so all decks are selected.)
        deck_elements = search_soup.select(
            "#latest-decks > div > div > div > div > div.d-flex.flex-column.text-left.p-2.rounded-bottom.deck_article-card-details.text-white > a"
        )
        print(f"Found {len(deck_elements)} deck elements on current page.")

        if not deck_elements:
            print("No deck elements found. Ending pagination.")
            break

        # Build a list of (deck URL, deck name) pairs.
        deck_list = []
        for elem in deck_elements:
            href = elem.get("href")
            name = elem.get_text(strip=True)
            if href:
                deck_url = href if href.startswith("http") else "https://ygoprodeck.com" + href
                deck_list.append((deck_url, name))
        print("Deck list extracted from current page.")

        # Save the current window handle (the search page).
        original_window = driver.current_window_handle

        # 2. Process each deck on the current page.
        for deck_url, deck_name in deck_list:
            print(f"\nProcessing deck '{deck_name}' ({deck_url})")
            # Open the deck detail in a new tab.
            driver.execute_script("window.open(arguments[0], '_blank');", deck_url)
            time.sleep(2)
            windows = driver.window_handles
            driver.switch_to.window(windows[-1])

            try:
                # Wait for the deck detail page to load (by waiting for the #main_deck element).
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#main_deck")))
                print("Deck detail page loaded.")

                # Parse the deck detail page.
                deck_html = driver.page_source
                deck_soup = BeautifulSoup(deck_html, "html.parser")

                # Locate deck sections.
                main_section = deck_soup.select_one("#main_deck")
                extra_section = deck_soup.select_one("#extra_deck")
                side_section = deck_soup.select_one("#side_deck")

                if main_section is None:
                    print("  Warning: Main deck container (#main_deck) not found.")
                if extra_section is None:
                    print("  Warning: Extra deck container (#extra_deck) not found.")
                if side_section is None:
                    print("  Warning: Side deck container (#side_deck) not found.")

                print("Extracting main deck card IDs...")
                main_cards = extract_card_ids(main_section)
                print("Extracting extra deck card IDs...")
                extra_cards = extract_card_ids(extra_section)
                print("Extracting side deck card IDs...")
                side_cards = extract_card_ids(side_section)

                # Build the YDK file content.
                ydk_lines = []
                ydk_lines.append("#main")
                ydk_lines.extend(main_cards)
                ydk_lines.append("#extra")
                ydk_lines.extend(extra_cards)
                ydk_lines.append("!side")
                ydk_lines.extend(side_cards)
                ydk_content = "\n".join(ydk_lines) + "\n"

                # Sanitize deck name for a safe filename.
                safe_deck_name = re.sub(r'[^A-Za-z0-9_\-]', '_', deck_name)
                filename = os.path.join(download_folder, safe_deck_name + ".ydk")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(ydk_content)
                print(f"Created YDK file: '{filename}'")
            except Exception as e:
                print("Error processing deck detail page:", e)
            finally:
                # Close the deck detail tab and return to the search page.
                driver.close()
                driver.switch_to.window(original_window)
                time.sleep(2)

        # 3. Attempt to navigate to the next page.
        try:
            # Hide any interfering ad iframes (those with IDs starting with "google_ads_iframe")
            driver.execute_script("""
                var adIframes = document.querySelectorAll('iframe[id^="google_ads_iframe"]');
                for (var i = 0; i < adIframes.length; i++) {
                    adIframes[i].style.display = 'none';
                }
            """)
            time.sleep(1)  # Allow time for the change to take effect

            # Wait for and click the next page button using JavaScript click.
            next_page_button = wait.until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "body > main > div > div > nav:nth-child(9) > div > button.btn.btn-primary.btn-block.d-inline.mt-0.ml-1.mr-1.prevDeck"
                ))
            )
            print("Clicking next page button...")
            driver.execute_script("arguments[0].click();", next_page_button)
            time.sleep(5)  # Wait for the next page to load.
        except Exception as e:
            print("Next page button not found or error:", e)
            break

except Exception as e:
    print("Error during run:", e)

finally:
    driver.quit()
    print("Webdriver closed.")
