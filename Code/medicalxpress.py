import requests
from bs4 import BeautifulSoup
import csv
import time
from tqdm import tqdm

# Base URL & Search URL
base_url = "https://www.hopkinsmedicine.org"
search_url = "https://www.hopkinsmedicine.org/search?q=multiple%20sclerosis&page="
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to scrape article details from a single page
def scrape_article_page(article_url):
    try:
        response = requests.get(article_url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract Title
        title_tag = soup.find("h1", class_="main-content__title")
        title = title_tag.text.strip() if title_tag else "N/A"

        # Extract Body Content
        content_tag = soup.find("article", class_="main-content")
        body_content = " ".join([p.text.strip() for p in content_tag.find_all("p")]) if content_tag else "N/A"

        # Organize the extracted data
        data = {
            "Title": title,
            "Body Content": body_content,
            "Source Link": article_url
        }

        return data

    except requests.exceptions.RequestException as e:
        print(f"Request error for {article_url}: {e}")
    except Exception as e:
        print(f"Error scraping {article_url}: {e}")
    return None

# Save scraped data to a CSV file
def save_to_csv(data, filename):
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Title", "Body Content", "Source Link"])
        writer.writeheader()
        writer.writerows(data)

# Main script
if __name__ == "__main__":
    article_urls = []

    # Construct URLs dynamically for 9 pages
    for page_num in range(1, 10):
        url = f"{search_url}{page_num}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract article links
            for a_tag in soup.select(".siteSearchResultContainer a.search-results-title"):
                article_url = a_tag["href"]
                if article_url.startswith("https"):
                    article_urls.append(article_url)

        except requests.exceptions.RequestException as e:
            print(f"Request error for page {page_num}: {e}")

    print(f"Total article URLs found: {len(article_urls)}")

    scraped_data = []
    for url in tqdm(article_urls, desc="Scraping Articles"):
        data = scrape_article_page(url)
        if data:
            scraped_data.append(data)
        time.sleep(1)  # Respect server

    # Save scraped data to CSV
    if scraped_data:
        save_to_csv(scraped_data, "multiple_sclerosis_HopkinsMedicine_articles.csv")
        print("Data saved to 'multiple_sclerosis_HopkinsMedicine_articles.csv'")
    else:
        print("No data scraped.")
