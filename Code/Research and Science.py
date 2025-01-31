from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time
import pandas as pd

# Set up the WebDriver
options = webdriver.ChromeOptions()
service = ChromeService(
    executable_path='C:\\Users\\Admin\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe')
driver = webdriver.Chrome(service=service, options=options)

driver.get('https://www.nationalmssociety.org/news-and-magazine/momentum-magazine/research-and-science')

# Wait for you to manually accept cookies
input("Please manually click 'Accept All Cookies' and then press Enter here to continue...")

# Click the "See More" button until all results are displayed
while True:
    try:
        see_more_button = driver.find_element(By.XPATH, '//button[@class="nmss-secondary-button"]')
        see_more_button.click()
        time.sleep(2)  # Wait for new content to load
    except NoSuchElementException:
        break


# Function to perform extraction with retries and explicit waits
def extract_with_retries(xpath, retries=2):
    attempt = 0
    while attempt < retries:
        try:
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element.text
        except (TimeoutException, StaleElementReferenceException):
            attempt += 1
            time.sleep(1)
    return "N/A"  # Return a default value if all retries fail


# Extract data from each magazine link
magazine_links = driver.find_elements(By.XPATH, '//a[@class="list-item"]')
data = []

for link in magazine_links:
    magazine_url = link.get_attribute('href')

    # Open the magazine link in a new tab
    driver.execute_script("window.open(arguments[0]);", magazine_url)
    driver.switch_to.window(driver.window_handles[1])
    time.sleep(2)  # Wait for the page to load

    try:
        # Extract data from the magazine page with retries
        title = extract_with_retries('//c-nmss-atom-title-header//h1')
        date = extract_with_retries('//div[@class="article-date"]/time')
        author = extract_with_retries('//div[@class="article-author"]')

        # Extract all text from the article
        content_elements = driver.find_elements(By.XPATH, '//c-nmss-atom-rich-text//span')
        content = ' '.join([elem.text for elem in content_elements])

        tags_elements = driver.find_elements(By.XPATH, '//ul[@class="article-tags"]/li/a/span[@class="link-label"]')
        tags = ', '.join([tag.text for tag in tags_elements]) if tags_elements else "N/A"

        data.append([title, date, author, content, tags, magazine_url])

        # Print title and date for verification
        print(f"Title: {title}")
        print(f"Date: {date}")  # Print the first 100 characters of content for brevity
    except Exception as e:
        print(f"Error processing {magazine_url}: {e}")

    # Close the tab and switch back to the main tab
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(2)  # Wait for the previous page to load

# Save data to an Excel file
df = pd.DataFrame(data, columns=['Title', 'Date', 'Author', 'Content', 'Tags', 'Link'])
df.to_excel('magazines.xlsx', index=False)

# Close the WebDriver
driver.quit()
