from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

# Set download directory
download_dir = os.path.join(os.getcwd(), "ydk_downloads")
os.makedirs(download_dir, exist_ok=True)

# Configure Chrome to auto-download files
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# Set up WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 10)

# Open the Deck Search Page
url = "https://ygoprodeck.com/deck-search/?sort=Deck%20Views&offset=0"
driver.get(url)

# Handle the cookie consent popup
try:
    consent_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]")))
    consent_button.click()
    print("Accepted cookie consent form.")
    time.sleep(2)
except Exception:
    print("No cookie consent popup detected.")

# Wait for decks to load
time.sleep(3)

# Scroll down to load more decks (adjust range for more scrolling)
for _ in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# Find all deck buttons
deck_buttons = driver.find_elements(By.CSS_SELECTOR, "button.deck_button")
print(f"Found {len(deck_buttons)} decks.")

# Iterate through decks
for i, button in enumerate(deck_buttons):
    try:
        print(f"Opening deck {i + 1}/{len(deck_buttons)}")

        # Click the deck button to open its page
        button.click()
        time.sleep(2)

        # Switch to the newly opened deck page
        driver.switch_to.window(driver.window_handles[-1])

        # Click the "More..." dropdown
        more_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'More')]")))
        more_button.click()
        time.sleep(1)

        # Click the .ydk download button
        ydk_download = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, ".ydk")))
        ydk_download.click()

        print("Download started.")

        # Wait for the file to download
        time.sleep(5)

        # Close the current tab and switch back to the main page
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        print(f"Failed to download .ydk: {e}")

# Close browser
driver.quit()

print(f"Downloads complete. Check the '{download_dir}' folder.")
