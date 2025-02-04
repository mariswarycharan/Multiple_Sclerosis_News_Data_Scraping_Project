import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm
from datetime import datetime
import time

# Base URL
base_url = 'https://www.news-medical.net'
# Headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Function to get article links from a search page
def get_article_links(search_url):
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    article_links = []

    # Find all <li class="result"> elements
    for result_item in soup.find_all('li', class_='result'):
        link_tag = result_item.find('a', href=True)
        if link_tag:
            article_links.append(base_url + link_tag['href'])

    print(f"Found {len(article_links)} articles on page {search_url}")
    return article_links

# Function to standardize the "Last Updated" date
def format_date(date_str):
    try:
        # Example: "Last Updated: Aug 21, 2023"
        if "Last Updated: " in date_str:
            date_str = date_str.replace("Last Updated: ", "").strip()
        formatted_date = datetime.strptime(date_str, "%b %d, %Y").strftime("%Y-%m-%d")
        return formatted_date
    except ValueError:
        return date_str  # Return the original string if formatting fails

# Function to scrape details from an article
def scrape_article(article_url):
    response = requests.get(article_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        # Extract Title
        title_tag = soup.find('h1', itemprop='headline')
        title = title_tag.get_text(strip=True) if title_tag else 'N/A'

        # Extract Author Name
        author_tag = soup.find('a', itemprop='url')
        author = author_tag.find('span', itemprop='name').get_text(strip=True) if author_tag and author_tag.find('span', itemprop='name') else 'N/A'

        # Extract Author Description
        author_info_tag = soup.find('div', class_='authorInfo col-xs-12 col-md-10')
        author_description = ''
        if author_info_tag:
            paragraphs = author_info_tag.find_all('p')
            if len(paragraphs) > 1:
                author_description = paragraphs[1].get_text(strip=True)

        # Extract Reviewed By (Name Only)
        reviewed_by_tag = soup.find('span', class_='article-meta-reviewer')
        reviewed_by = reviewed_by_tag.find('a').get_text(strip=True) if reviewed_by_tag and reviewed_by_tag.find('a') else 'N/A'

        # Extract Content between <hr> tags
        content = ''
        article_body = soup.find('div', id='ctl00_cphBody_divText', itemprop='articleBody')
        if article_body:
            for element in article_body.find_all(['h2', 'p']):
                if element.name == 'h2':
                    content += f"\n{element.get_text(strip=True)}\n"
                elif element.name == 'p':
                    content += f"{element.get_text(strip=True)}\n"

        content = content.strip()

        # Extract Last Updated Date
        date_tag = soup.find('p', class_='updated-dates')
        date = format_date(date_tag.get_text(strip=True)) if date_tag else 'N/A'

        # Extract Citations
        citations_tag = soup.find('div', class_='content-citations-wrapper')
        citations = ' '.join([citation.get_text(strip=True) for citation in citations_tag.find_all('p')]) if citations_tag else 'N/A'

        # Extract References
        references_tag = soup.find('ul')
        references = ', '.join([li.get_text(strip=True) for li in references_tag.find_all('li')]) if references_tag else 'N/A'

        return {
            'Title': title,
            'Author': author,
            'Author Description': author_description,
            'Reviewed By': reviewed_by,
            'Content': content,
            'Last Updated': date,
            'Citations': citations,
            'References': references,
            'Article Link': article_url
        }
    except Exception as e:
        print(f"Error scraping {article_url}: {e}")
        return None

# Create CSV file and write headers
csv_file = 'news_medical_articles_sequential_health.csv'
with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow([
        'Title', 'Author', 'Author Description', 'Reviewed By', 'Content', 'Last Updated',
        'Citations', 'References', 'Article Link'
    ])

# Loop through all 225 pages with progress bar
for page_num in tqdm(range(1, 226), desc='Pages'):  # 225 pages
    search_url = f'https://www.news-medical.net/medical/search?q=Multiple+Sclerosis&t=health&page={page_num}'
    article_links = get_article_links(search_url)

    for link in tqdm(article_links, desc=f'Articles on Page {page_num}', leave=False):
        article_data = scrape_article(link)

        if article_data:
            # Append article data to CSV file
            with open(csv_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    article_data['Title'],
                    article_data['Author'],
                    article_data['Author Description'],
                    article_data['Reviewed By'],
                    article_data['Content'],
                    article_data['Last Updated'],
                    article_data['Citations'],
                    article_data['References'],
                    article_data['Article Link']
                ])

        # Delay between requests to prevent overloading the server
        time.sleep(1)

print('Data scraping complete. Data saved to CSV file.')
