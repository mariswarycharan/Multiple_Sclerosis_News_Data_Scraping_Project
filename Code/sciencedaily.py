import os
import time
import random
import csv
import threading
from queue import Queue
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Constants
BASE_URL = "https://www.sciencedaily.com"
SEARCH_URL = "https://www.sciencedaily.com/search/?keyword=Multiple+Sclerosis#gsc.tab=0&gsc.q=Multiple%20Sclerosis&gsc.page="
TOTAL_PAGES = 989
THREAD_COUNT = 10  # Number of parallel threads
CSV_FILENAME = "science_daily_articles.csv"
URL_QUEUE = Queue()
CSV_LOCK = threading.Lock()

# Set up Selenium options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in background
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")


# Initialize WebDriver
def get_driver():
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


# Fetch article links using Selenium (bypasses CAPTCHA)
def fetch_article_links():
    print(f"🔍 Extracting article links from {TOTAL_PAGES} pages...")
    driver = get_driver()

    all_links = set()

    for page in tqdm(range(1, TOTAL_PAGES + 1), desc="Fetching article links"):
        driver.get(f"{SEARCH_URL}{page}")
        time.sleep(random.uniform(3, 6))  # Random delay to mimic human behavior

        # Extract article links
        links = driver.find_elements(By.CSS_SELECTOR, ".gs-title a")
        for link in links:
            url = link.get_attribute("href")
            if url and "/releases/" in url:
                all_links.add(url)

    driver.quit()
    print(f"✅ Total articles found: {len(all_links)}")

    # Save unique links to queue
    for link in all_links:
        URL_QUEUE.put(link)


# Scrape article details
def scrape_article(article_url):
    headers = {"User-Agent": "Mozilla/5.0"}

    for _ in range(3):  # Retry 3 times if request fails
        try:
            response = requests.get(article_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            title = soup.find("h1", {"id": "headline"})
            title = title.text.strip() if title else "N/A"

            subtitle = soup.find("h2", {"id": "subtitle"})
            subtitle = subtitle.text.strip() if subtitle else "N/A"

            date = soup.find("dd", {"id": "date_posted"})
            date = date.text.strip() if date else "N/A"

            source = soup.find("dd", {"id": "source"})
            source = source.text.strip() if source else "N/A"

            summary = soup.find("dd", {"id": "abstract"})
            summary = summary.text.strip() if summary else "N/A"

            full_story_div = soup.find("div", {"id": "story_text"})
            full_story = " ".join(p.text.strip() for p in full_story_div.find_all("p")) if full_story_div else "N/A"

            journal_ref = soup.find("ol", class_="journal")
            journal_ref = " ".join(journal_ref.text.strip().split("\n")) if journal_ref else "N/A"

            article_url_meta = soup.find("meta", {"id": "og_url"})
            article_url = article_url_meta["content"] if article_url_meta else article_url

            return {
                "Title": title,
                "Subtitle": subtitle,
                "Date": date,
                "Source": source,
                "Summary": summary,
                "Full Story": full_story,
                "Journal Reference": journal_ref,
                "Original Article URL": article_url,
            }
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching {article_url}: {e}")
            time.sleep(random.uniform(2, 5))
    return None


# Worker function to process articles
def worker():
    while not URL_QUEUE.empty():
        article_url = URL_QUEUE.get()
        data = scrape_article(article_url)
        if data:
            with CSV_LOCK:
                save_to_csv([data], CSV_FILENAME)
        URL_QUEUE.task_done()


# Save extracted data to CSV
def save_to_csv(data, filename):
    with open(filename, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Title", "Subtitle", "Date", "Source", "Summary", "Full Story",
                                                  "Journal Reference", "Original Article URL"])
        if file.tell() == 0:
            writer.writeheader()
        writer.writerows(data)


# Main function
def main():
    # Step 1: Fetch article links
    fetch_article_links()

    # Step 2: Start multi-threaded scraping
    print(f"🚀 Starting scraping with {THREAD_COUNT} threads...")
    threads = []
    for _ in range(THREAD_COUNT):
        thread = threading.Thread(target=worker)
        thread.start()
        threads.append(thread)

    # Step 3: Wait for all threads to finish
    URL_QUEUE.join()

    print(f"✅ Data saved to {CSV_FILENAME}")


# Run script
if __name__ == "__main__":
    main()
