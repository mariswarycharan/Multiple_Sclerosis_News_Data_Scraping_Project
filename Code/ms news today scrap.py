import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm

# Base URL of the website
base_url = 'https://multiplesclerosisnewstoday.com'

# Define headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


# Function to get article links from a search page
def get_article_links(search_url):
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    article_links = []

    # Find all a tags with the class bio-link bio-link--title
    for a_tag in soup.find_all('a', class_='bio-link bio-link--title', href=True):
        article_links.append(a_tag['href'])

    print(f"Found {len(article_links)} articles on page {search_url}")
    return article_links


# Function to scrape details from an article
def scrape_article(article_url):
    response = requests.get(article_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        # Extract required details with default values if not found
        heading = soup.find('h1', class_='bio-article-content-heading bio-type-display--large')
        heading = heading.text.strip() if heading else 'N/A'

        description = soup.find('p', class_='bio-article-content-lede bio-type-display--small')
        description = description.text.strip() if description else 'N/A'

        author_tag = soup.find('span', class_='bio-avatar-author--name')
        author_link_tag = author_tag.find('a') if author_tag else None
        author = author_link_tag.text.strip() if author_link_tag else 'N/A'
        author_link = base_url + author_link_tag['href'] if author_link_tag else 'N/A'

        date = soup.find('time')
        date = date['datetime'] if date else 'N/A'

        # Capture the entire news content
        news_paragraphs = soup.select('div.bio-article-body p')
        news_mentioned = '\n'.join([p.get_text(separator=' ', strip=True) for p in news_paragraphs])
        news_mentioned = news_mentioned.strip() if news_mentioned else 'N/A'

        about_author_tag = soup.select_one('.bio-avatar-description')
        about_author = about_author_tag.get_text(separator=' ', strip=True) if about_author_tag else 'N/A'

        # Collect all tags
        tags = [tag.text.strip() for tag in soup.select('.bio-article-tags a.bio-link.bio-link--primary')]
        tags = ', '.join(tags) if tags else 'N/A'

        return {
            'heading': heading,
            'description': description,
            'author': author,
            'author_link': author_link,
            'date': date,
            'news_mentioned': news_mentioned,
            'about_author': about_author,
            'tags': tags
        }
    except Exception as e:
        print(f"Error scraping {article_url}: {e}")
        return None


# Create CSV file and write headers
csv_file = 'news_articles_output.csv'  # Renamed to avoid potential file lock issues
with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(
        ['Heading', 'Description', 'Author', 'Author Link', 'Date', 'News Mentioned', 'About Author', 'Tags'])

# Loop through all pages with progress bar
for page_num in tqdm(range(1, 177), desc='Pages'):
    search_url = f'https://multiplesclerosisnewstoday.com/category/news-posts/page/{page_num}/'
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
                    article_data['heading'],
                    article_data['description'],
                    article_data['author'],
                    article_data['author_link'],
                    article_data['date'],
                    article_data['news_mentioned'],
                    article_data['about_author'],
                    article_data['tags']
                ])

print('Data scraped and saved to CSV file.')
