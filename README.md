# YGOPRODeck YDK Scraper

This script automates the process of scraping Yu-Gi-Oh! deck data from [YGOPRODeck](https://ygoprodeck.com) and generates YDK files (which list card IDs) for each deck found. It uses Selenium to handle dynamic content (including cookie consent, deck navigation, and pagination) and BeautifulSoup to parse the HTML for the required deck information.

## How It Works

1. **Initial Setup and Consent:**
   - The script initializes a Selenium WebDriver (using Chrome) and opens the deck search page.
   - It waits for and clicks the cookie consent popup.

2. **Pagination and Deck Extraction:**
   - The search URL contains an `offset` parameter. The script starts at offset `0` and iterates through the search result pages.
   - For each page, it waits for the deck container (identified by the CSS class `deck-searcher-bottom-pane`) to load.
   - The page HTML is then parsed with BeautifulSoup to extract all deck links. Each deck link is an `<a>` element with the class:
     ```
     stretched-link text-decoration-none text-reset text-truncate deck_article-card-title
     ```
   - The script extracts the deck's URL and name from these elements.

3. **Processing Each Deck:**
   - For every deck link found, the script opens the deck detail page in a new browser tab.
   - It waits until the main deck section (`#main_deck`) is present, ensuring that the deck details have fully loaded.

4. **Extracting Deck Data:**
   - The deck detail page is parsed with BeautifulSoup.
   - The script locates the three deck sections using their IDs: `#main_deck`, `#extra_deck`, and `#side_deck`.
   - It extracts card IDs from each section by finding all `<img>` tags with the class `lazy master-duel-card` and reading their `data-name` attribute.

5. **Building and Saving the YDK File:**
   - The extracted card IDs are formatted into the YDK file structure:
     - `#main` followed by the main deck card IDs,
     - `#extra` followed by the extra deck card IDs, and
     - `!side` followed by the side deck card IDs.
   - The deck’s name is sanitized (removing invalid filename characters) and used as the filename.
   - The YDK file is saved into a folder named `ydk_download` in the code directory.

6. **Iterating Through All Pages:**
   - After processing all decks on a search page, the script increments the offset (by 20) and loads the next page.
   - This continues until no more deck links are found on a page.

7. **Cleanup:**
   - After processing each deck, its detail tab is closed and the script returns to the search page.
   - Finally, the WebDriver is closed.

## Usage

1. **Install Dependencies:**

   Make sure you have installed the required Python packages:

   ```bash
   pip install selenium beautifulsoup4
   ```

2. **Configure ChromeDriver:**

   Ensure that the `CHROMEDRIVER_PATH` in the script is set to the correct path where your ChromeDriver is located.

3. **Run the Script:**

   Execute the script from your terminal:

   ```bash
   python your_script_name.py
   ```

   The generated YDK files will be saved in the `ydk_download` folder.
