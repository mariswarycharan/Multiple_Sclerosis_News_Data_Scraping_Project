import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd

def get_data_one_article(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    data = {'complete_content': '', 'writter_details': ''}
    try:
        response = requests.get(link, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        whole_content = soup.find('div', class_='entry-content col-md-9 col-md-push-3')

        if whole_content:
            data['complete_content'] = whole_content.text.strip()
            
            try: 
                writter_details = whole_content.find_all('p')[-1].text.strip()
                data['writter_details'] = writter_details
            except:
                data['writter_details'] = ''
        else:
            print(f"Warning: Content not found for {link}")
            whole_content = soup.find('div', class_='entry-content col-md-9 col-md-push-3 news-spec-sidebar-1')
            if whole_content:
                data['complete_content'] = whole_content.text.strip()
            else:
                print(f"again Warning: Content again not found for {link}")
            
    except requests.RequestException as e:
        print(f"Request error for {link}: {e}")
    except Exception as e:
        print(f"Error processing article {link}: {e}")
    return data

def get_data(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    all_data = []
    try:
        response = requests.get(link, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        main_div = soup.find('div', class_='js-wpv-view-layout js-wpv-layout-responsive js-wpv-view-layout-24823')
        if not main_div:
            print(f"Warning: Main div not found for {link}")
            return all_data

        article_div = main_div.find_all('div', attrs={'style': 'border-bottom: 1px solid #999999; padding-bottom: 20px; margin-bottom: 30px;'})
        
        for idx,doctor in enumerate(article_div):
            print(f"Processing article {idx+1}")
            try:
                title = doctor.find('h2').text.strip()
                link = doctor.find('a')['href']
                published_date = doctor.find('span', class_='entry-date published').text.strip()
                
                data_from_article = get_data_one_article(link)
                doctor_info = {
                    'title': title,
                    'link': link,
                    'date': published_date,
                    'complete_content': data_from_article['complete_content'],
                    'writter_details': data_from_article['writter_details']
                }
                all_data.append(doctor_info)
            except AttributeError as e:
                print(f"Parsing error: {e}")
                all_data.append({'title': 'error', 'link': 'error', 'date': 'error', 'complete_content': 'error', 'writter_details': 'error'})
            except Exception as e:
                print(f"Unexpected error: {e}")
                all_data.append({'title': 'error', 'link': 'error', 'date': 'error', 'complete_content': 'error', 'writter_details': 'error'})
    except requests.RequestException as e:
        print(f"Request error for {link}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return all_data


doctor_list_all = []
for i in tqdm(range(1, 30)):
    print(f"Processing page {i}")
    try:
        url = f"https://mymsaa.org/news/page/{i + 1}"
        data = get_data(url)
        doctor_list_all.extend(data)
        print(f"Processed page {i+1}")
    except Exception as e:
        print(f"Error processing page {i+1}: {e}")

try:
    df = pd.DataFrame(doctor_list_all, columns=['title', 'link', 'date', 'complete_content', 'writter_details'])
    df.to_excel('Output/msaa_data.xlsx', index=False)
    print("Data saved successfully.")
except Exception as e:
    print(f"Error saving data to Excel: {e}")
