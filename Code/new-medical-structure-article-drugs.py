import requests
from bs4 import BeautifulSoup
import csv
import time
from tqdm import tqdm
import re
import os

# Base URL & Search URL
base_url = "https://www.news-medical.net"
search_url = "https://www.news-medical.net/medical/search?q=Multiple+Sclerosis&t=drugs&page="
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to extract drug URLs from search results
def get_drug_links():
    drug_urls = set()  # Using a set to prevent duplicate links

    for page_num in range(1, 10):  # Loop through first 9 pages
        url = f"{search_url}{page_num}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract drug links
            for a_tag in soup.find_all("a", href=True):
                if "/drugs/" in a_tag["href"]:
                    full_url = base_url + a_tag["href"]
                    drug_urls.add(full_url)  # Using set ensures no duplicates

            print(f"✅ Page {page_num}: {len(drug_urls)} unique links collected.")

        except requests.exceptions.RequestException as e:
            print(f"❌ Request error for page {page_num}: {e}")

        time.sleep(1)  # Respect server

    print(f"🔹 Total unique drug pages found: {len(drug_urls)}")
    return list(drug_urls)


# Function to scrape drug details from a single page
def scrape_drug_page(drug_url):
    try:
        response = requests.get(drug_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract Title
        title = soup.find("h1").text.strip() if soup.find("h1") else "N/A"

        # Extract Active Ingredient
        active_ingredient_tag = soup.find("div", class_="label-expl",
                                          string=re.compile(r"contains the active ingredient", re.I))
        active_ingredient = (
            active_ingredient_tag.text.split("contains the active ingredient")[-1].split(".")[0].strip()
            if active_ingredient_tag else "N/A"
        )

        # Extract Sections with Keywords
        def extract_section(keyword):
            section = soup.find("h2", string=lambda x: x and keyword in x)
            return section.find_next("div").text.strip() if section else "N/A"

        purpose = extract_section("Why am I using")
        before_use = extract_section("What should I know before I use")
        dosage = extract_section("How do I use")
        side_effects = extract_section("Are there any side effects")
        product_details = extract_section("Product details")

        # Extract Full Content Body
        content_section = soup.find("div", class_="content drug-page-content clearfix")
        full_content = " ".join(content_section.stripped_strings) if content_section else "N/A"

        # Split Full Content into Two Parts
        split_keyword = "5. What should I know while using Ocrevus?"
        split_index = full_content.find(split_keyword)

        part_1 = full_content[:split_index].strip() if split_index != -1 else full_content
        part_2 = full_content[split_index:].strip() if split_index != -1 else "N/A"

        # Organize extracted data
        data = {
            "Title": title,
            "Active Ingredient": active_ingredient,
            "Purpose": purpose,
            "Before Use": before_use,
            "Dosage": dosage,
            "Side Effects": side_effects,
            "Product Details": product_details,
            "Full Content Part 1": part_1,
            "Full Content Part 2": part_2,
            "Source Link": drug_url
        }

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error for {drug_url}: {e}")
    except Exception as e:
        print(f"❌ Error scraping {drug_url}: {e}")
    return None


# Save scraped data to a CSV file
def save_to_csv(data, filename):
    file_exists = os.path.isfile(filename)

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)


# Main script
if __name__ == "__main__":
    drug_urls = get_drug_links()

    scraped_data = []
    for url in tqdm(drug_urls, desc="Scraping Drug Pages"):
        data = scrape_drug_page(url)
        if data:
            scraped_data.append(data)
        time.sleep(1)  # Respect server

    # Save scraped data to CSV
    if scraped_data:
        save_to_csv(scraped_data, "drug_details_news_medical.csv")
        print("✅ Data saved to 'drug_details_news_medical.csv'")
    else:
        print("❌ No data scraped.")
