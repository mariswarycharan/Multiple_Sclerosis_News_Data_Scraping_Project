import requests
from bs4 import BeautifulSoup
import csv
import time
from tqdm import tqdm

# Define base URL and headers
base_url = 'https://www.news-medical.net'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Function to scrape drug details from a single page
def scrape_drug_page(drug_url):
    try:
        response = requests.get(drug_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract drug details
        title = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'

        active_ingredient_tag = soup.find('b', string='Active ingredient:')
        active_ingredient = active_ingredient_tag.find_next('i').text.strip() if active_ingredient_tag else 'N/A'

        purpose_section = soup.find('h2', string=lambda x: x and 'Why am I using' in x)
        purpose = purpose_section.find_next('div').text.strip() if purpose_section else 'N/A'

        before_use_section = soup.find('h2', string=lambda x: x and 'What should I know before I use' in x)
        before_use = before_use_section.find_next('div').text.strip() if before_use_section else 'N/A'

        try:
            # Locate the div with the specified ID for "What if I am taking other medicines?"
            taking_medicines_div = soup.find('div', {'id': '475670-1-1'})

            if taking_medicines_div:
                # Extract all child elements with the class 'label-expl' and 'label-expldot1'
                content = []
                for item in taking_medicines_div.find_all(['div'], class_=['label-expl', 'label-expldot1']):
                    content.append(item.get_text(strip=True))

                # Combine the extracted text into a single string
                taking_medicines = "\n".join(content)
            else:
                taking_medicines = "N/A"
        except Exception as e:
            print(f"Error extracting 'Taking Other Medicines' section: {e}")
            taking_medicines = "N/A"

        dosage_section = soup.find('h2', string=lambda x: x and 'How do I use' in x)
        dosage = dosage_section.find_next('div').text.strip() if dosage_section else 'N/A'

        side_effects_section = soup.find('h2', string=lambda x: x and 'Are there any side effects' in x)
        side_effects = side_effects_section.find_next('div').text.strip() if side_effects_section else 'N/A'

        product_details_section = soup.find('h2', string=lambda x: x and 'Product details' in x)
        product_details = product_details_section.find_next('div').text.strip() if product_details_section else 'N/A'

        # Return extracted data as a dictionary
        return {
            'Title': title,
            'Active Ingredient': active_ingredient,
            'Purpose': purpose,
            'Before Use': before_use,
            'Taking Other Medicines': taking_medicines,
            'Dosage': dosage,
            'Side Effects': side_effects,
            'Product Details': product_details,
            'URL': drug_url
        }

    except Exception as e:
        print(f"Error scraping {drug_url}: {e}")
        return None

# Save scraped data to a CSV file
def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

# Main script
if __name__ == '__main__':
    # Construct URLs dynamically for 87 pages
    drug_urls = []
    for page_num in range(1, 88):
        search_url = f'https://www.news-medical.net/medical/search?q=Multiple+Sclerosis&t=drugs&page={page_num}'
        try:
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract article links from the search page
            for a_tag in soup.find_all('a', href=True):
                if '/drugs/' in a_tag['href']:
                    full_url = base_url + a_tag['href']
                    if full_url not in drug_urls:
                        drug_urls.append(full_url)
        except Exception as e:
            print(f"Error fetching page {page_num}: {e}")

    print(f"Total drug URLs found: {len(drug_urls)}")

    scraped_data = []

    for url in tqdm(drug_urls, desc='Scraping Drug Pages'):
        data = scrape_drug_page(url)
        if data:
            scraped_data.append(data)
        time.sleep(1)  # Respect server by adding a delay

    # Save the scraped data to a CSV file
    if scraped_data:
        save_to_csv(scraped_data, 'drug_details3.csv')
        print("Data saved to 'drug_details.csv'")
    else:
        print("No data scraped.")
