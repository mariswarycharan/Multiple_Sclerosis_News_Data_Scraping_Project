import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm

# Base URL of the website
base_url = 'https://www.biospace.com'

# Search URL
search_url_template = 'https://www.biospace.com/search?q=multiple%20sclerosis&f2=7d984112-0772-3a35-93aa-34c50aaf2ffd&f5=00000190-7930-d426-a39a-ffb535680001&f5=00000190-7930-d171-a1d5-f9fa99940001&f5=00000190-7931-d426-a39a-ffb501f70001&f5=00000190-7931-d426-a39a-ffb522300001&f5=00000190-7931-d171-a1d5-f9fb8f970001&f5=00000190-7931-d171-a1d5-f9fbb6690001&f5=00000190-7932-d171-a1d5-f9fac8c50001&f5=00000190-7932-d426-a39a-ffb7ed6e0001&f5=00000190-7933-d171-a1d5-f9fb35580001&f5=00000190-7934-d426-a39a-ffb550390001&f5=00000190-7934-d171-a1d5-f9fe93ed0001&f5=00000190-7934-d426-a39a-ffb5b04b0000&f5=00000190-7a34-d4d8-a3b5-fb7d64a80001&f5=00000190-7935-d171-a1d5-f9ff31c00001&f5=0000018f-a6fb-d495-abcf-a6ffccf70000&f5=00000190-7a34-d4d8-a3b5-fb7dbd0b0001&f5=00000190-7936-d171-a1d5-f9fe00d60001&f5=00000190-7936-d426-a39a-ffb7201c0001&f5=00000190-7936-d171-a1d5-f9fe7e410001&s=0&f0=&f1=&f4=&p={page}'

# Define headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Function to get article links from a search page
def get_article_links(search_url):
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    article_links = []

    # Locate the <ul> element containing all search results
    search_results = soup.find('ul', class_='SearchResultsModule-results')

    # Iterate over each <li> to find article links
    if search_results:
        for li in search_results.find_all('li', class_='SearchResultsModule-results-item'):
            title_div = li.find('div', class_='PagePromo-title')
            if title_div:
                link_tag = title_div.find('a', class_='Link', href=True)
                if link_tag:
                    article_links.append(link_tag['href'])

    print(f"Found {len(article_links)} articles on page {search_url}")
    return article_links

# Function to scrape details from an article
def scrape_article(article_url):
    response = requests.get(article_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        # Extract title
        title_tag = soup.find('h1', class_='Page-headline')
        title = title_tag.text.strip() if title_tag else 'N/A'

        # Extract date
        date_tag = soup.find('div', class_='Page-datePublished')
        date = date_tag.text.strip() if date_tag else 'N/A'

        # Extract author name
        author_tag = soup.find('div', class_='PagePromo-author')
        author = author_tag.find('a').text.strip() if author_tag and author_tag.find('a') else 'N/A'

        # Extract author description
        author_description_tag = soup.find('div', class_='Author-bio')
        author_description = author_description_tag.get_text(separator=' ', strip=True) if author_description_tag else 'N/A'

        # Extract content body
        article_body_tag = soup.find('div', class_='Page-articleBody')
        if article_body_tag:
            subheadline_tag = article_body_tag.find('h2', class_='Page-subHeadline')
            subheadline = subheadline_tag.text.strip() if subheadline_tag else ''

            rich_text_body_tag = article_body_tag.find('div', class_='RichTextArticleBody')
            content_paragraphs = [p.get_text(separator=' ', strip=True) for p in rich_text_body_tag.find_all('p')] if rich_text_body_tag else []

            content_body = subheadline + '\n' + '\n'.join(content_paragraphs)
        else:
            content_body = 'N/A'

        return {
            'title': title,
            'date': date,
            'author': author,
            'author_description': author_description,
            'content_body': content_body,
            'source_link': article_url  # Include the source link
        }
    except Exception as e:
        print(f"Error scraping {article_url}: {e}")
        return None

# Create CSV file and write headers
csv_file = 'biospace_articles.csv'
with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Title', 'Date', 'Author', 'Author Description', 'Content Body', 'Source Link'])

# Loop through all pages with progress bar
for page_num in tqdm(range(1, 12), desc='Pages'):
    search_url = search_url_template.format(page=page_num)
    article_links = get_article_links(search_url)

    for link in tqdm(article_links, desc='Articles', leave=False):
        # Construct full URL if the link is relative
        full_link = link if link.startswith('http') else base_url + link

        article_data = scrape_article(full_link)

        if article_data:
            # Append article data to CSV file
            with open(csv_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    article_data['title'],
                    article_data['date'],
                    article_data['author'],
                    article_data['author_description'],
                    article_data['content_body'],
                    article_data['source_link']  # Write the source link
                ])

print('Data scraping completed and saved to CSV file.')
