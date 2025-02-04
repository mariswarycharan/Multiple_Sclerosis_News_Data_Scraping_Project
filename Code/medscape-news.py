import logging
import time
import csv
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Selenium WebDriver setup
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Enable persistent browser session
chrome_options.add_argument(r"C:\\Users\\M.HARISH\\Documents\\chrome_profile")  # Set a persistent browser profile

# **Update the correct path to your ChromeDriver**
service = Service(r"C:\Users\M.HARISH\Documents\chrome driver\chromedriver-win64\chromedriver.exe")

# Start WebDriver
driver = webdriver.Chrome(service=service, options=chrome_options)

# **Step 1: Open the login page and wait for manual login**
login_url = "https://www.medscape.com"
driver.get(login_url)

input("Log in manually, then press Enter to continue...")  # Wait for manual login

logging.info("Login successful! Proceeding with article scraping...")

# Base URL and search URL template
search_url_template = "https://search.medscape.com/search/?q=multiple%20sclerosis&&plr=nws&page={page}"

def get_article_links(driver, search_url):
    logging.info(f"Fetching search URL: {search_url}")
    driver.get(search_url)
    article_links = []

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'searchResult')))
        search_results = driver.find_elements(By.CLASS_NAME, 'searchResult')

        for result in search_results:
            try:
                link_tag = result.find_element(By.TAG_NAME, 'a')
                if link_tag:
                    full_url = link_tag.get_attribute('href')
                    if full_url and "article" in full_url:
                        logging.info(f"Found article link: {full_url}")
                        article_links.append(full_url)
            except Exception as e:
                logging.warning(f"Skipping result due to error: {e}")

    except Exception as e:
        logging.error(f"Error extracting article links: {e}")

    return article_links

def scrape_medscape_article(driver, article_url):
    """
    Scrapes a Medscape article, extracting title, author, date, content (split into 3 parts), and source link.
    """
    logging.info(f"Scraping article: {article_url}")
    driver.get(article_url)
    time.sleep(3)  # Allow page to load

    # Scroll down to trigger lazy-loaded content
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(2)

    # Expand full content if a 'Load More' button exists
    try:
        load_more_button = driver.find_element(By.CLASS_NAME, "pager__ButtonStyled-sc-1i8e93j-1")
        ActionChains(driver).move_to_element(load_more_button).click().perform()
        time.sleep(2)
    except Exception:
        pass  # No load more button found, continue

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Extract Title (Handling multiple formats)
    title = "No Title Found"
    title_element = soup.find("h1", class_="article__title")
    if not title_element:
        title_element = soup.find("h1", class_="title")  # Alternate title format
    if title_element:
        title = title_element.text.strip()

    # Extract Author Name (Keep previous extraction logic)
    author_element = soup.select_one(".meta__author-name, .meta-author")
    author_name = author_element.text.strip() if author_element else "No Author Found"

    # Extract Date (Keep previous extraction logic)
    date_element = soup.select_one(".meta__date span.article-date, .meta-date")
    date = date_element.text.strip() if date_element else "No Date Found"

    # Extract Content Body (Handle multiple formats & Remove ads/images/videos)
    content_body = []
    content_sections = soup.select("div.article__main-content p, div.article__content p, div#article-content p")

    for section in content_sections:
        if section.find("img") or section.find("video"):  # Skip media elements
            continue
        text = section.get_text(strip=True)
        if text:
            content_body.append(text)

    full_content = "\n\n".join(content_body) if content_body else "No Content Found"

    # Split Content into Three Parts (Even Distribution)
    content_length = len(full_content)
    part1 = full_content[:content_length // 3].strip()
    part2 = full_content[content_length // 3: 2 * (content_length // 3)].strip()
    part3 = full_content[2 * (content_length // 3):].strip()

    # Extract Source Link
    source_link = article_url

    return {
        "Title": title,
        "Author": author_name,
        "Date": date,
        "Part1": part1,
        "Part2": part2,
        "Part3": part3,
        "Source Link": source_link
    }

if __name__ == '__main__':
    scraped_data = []

    try:
        for page_num in tqdm(range(151, 325), desc="Pages"):  # Scrape multiple pages
            search_url = search_url_template.format(page=page_num)
            article_links = get_article_links(driver, search_url)

            for article_url in tqdm(article_links, desc="Articles", leave=False):
                article_data = scrape_medscape_article(driver, article_url)
                if article_data:
                    scraped_data.append(article_data)

                time.sleep(1)  # Avoid overloading the server

        # Save Data to CSV
        csv_filename = "medscape_articles.csv"
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["Title", "Author", "Date", "Part1", "Part2", "Part3", "Source Link"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(scraped_data)

        logging.info(f"Data saved successfully in {csv_filename}")
    finally:
        driver.quit()
        logging.info("WebDriver session closed.")
