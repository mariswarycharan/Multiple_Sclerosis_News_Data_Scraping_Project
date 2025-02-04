import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm
import time

# Base URL and search URL
base_url = 'https://www.webmd.com'
search_url = 'https://www.webmd.com/multiple-sclerosis/news/default.htm'

# Define headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Function to get article links from the search page
def get_article_links(search_url):
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    article_links = []

    # Extract links from the main article list
    latest_section = soup.find('div', class_='latest')
    if latest_section:
        latest_link = latest_section.find('a', href=True)
        if latest_link:
            article_links.append(latest_link['href'])

    list_section = soup.find('ul', class_='list')
    if list_section:
        for li in list_section.find_all('li'):
            link_tag = li.find('a', href=True)
            if link_tag:
                article_links.append(link_tag['href'])

    return [link if link.startswith('http') else base_url + link for link in article_links]

# Function to scrape details from an article
def scrape_article(article_url):
    response = requests.get(article_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        # Extract Title
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else 'N/A'

        # Extract Author Name
        author_tag = soup.find('span', class_='person')
        author = author_tag.text.strip() if author_tag else 'N/A'

        # Extract Content Body
        content_body = []
        content_section = soup.find('div', class_='article__body')
        if content_section:
            paragraphs = content_section.find_all('p')
            for paragraph in paragraphs:
                content_body.append(paragraph.get_text(separator=' ', strip=True))

        # Extract Related Source
        source_section = soup.find('div', class_='sources-section')
        related_source = ''
        source_link = ''
        if source_section:
            source_paragraph = source_section.find('p')
            related_source = source_paragraph.text.strip() if source_paragraph else 'N/A'

            # Extract source link if present
            source_anchor = source_section.find('a', href=True)
            source_link = source_anchor['href'] if source_anchor else 'N/A'

        return {
            'Title': title,
            'Author': author,
            'Content Body': '\n'.join(content_body),
            'URL': article_url
        }

    except Exception as e:
        print(f"Error scraping {article_url}: {e}")
        return None

# Save data to CSV file
def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['Title', 'Author', 'Content Body', 'URL'])
        writer.writeheader()
        writer.writerows(data)

# Main script
if __name__ == '__main__':
    csv_file = 'webmd_multiple_sclerosis_articles.csv'
    scraped_data = []

    # Get article links from the search page
    print("Fetching article links...")
    article_links = get_article_links(search_url)

    print(f"Found {len(article_links)} articles.")

    # Scrape each article
    for url in tqdm(article_links, desc='Scraping Articles'):
        article_data = scrape_article(url)
        if article_data:
            scraped_data.append(article_data)
        time.sleep(1)  # Respectful delay

    # Save the scraped data to a CSV file
    if scraped_data:
        save_to_csv(scraped_data, csv_file)
        print(f"Data saved to {csv_file}")
    else:
        print("No data scraped.")
