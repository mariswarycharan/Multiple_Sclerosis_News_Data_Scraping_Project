import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd

def get_data_one_article(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    data = {'complete_content': '', 'author_bio': ''}
    try:
        response = requests.get(link, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        whole_content = soup.find('div', class_='post-content')
        
        if whole_content:
            data['complete_content'] = whole_content.text.strip()
        else:
            print(f"Warning: Content not found for {link}")
            
        try: 
            author_bio = soup.find('div', class_='author-card').text.strip()
            data['author_bio'] = author_bio
        except:
            data['author_bio'] = ''
            print(f"Warning: Author bio not found for {link}")
            
    
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
        main_div = soup.find('div', {'itemprop': 'mainEntityOfPage', 'data-gated': True})
        
        if not main_div:
            print(f"Warning: Main div not found for {link}")
            return all_data

        article_div = main_div.find_all('article' , class_='list-card show-excerpt')
        
        for idx,doctor in enumerate(article_div):
            print(f"Processing article {idx+1}")
            try:
                link = doctor.find('a')['href']
                title = doctor.find('div', class_='title').text.strip()
                author = doctor.find('div', class_='post-bylines').text.strip()
                author_profile_link = "https://www.rarediseaseadvisor.com/" + doctor.find('div', class_='post-bylines').find('a')['href']
                published_date = doctor.find('time', {'class': 'post-time -published'}).text.strip()
                                
                data_from_article = get_data_one_article(link)
                
                doctor_info = {
                    'title': title,
                    'link': link,
                    'date': published_date,
                    'author': author,
                    'author_profile_link': author_profile_link,
                    'author_bio': data_from_article['author_bio'],
                    'complete_content': data_from_article['complete_content'],
                }
                all_data.append(doctor_info)
                
            except AttributeError as e:
                print(f"Parsing error: {e}")
                all_data.append({'title': 'error', 'link': 'error', 'date': 'error', 'author': 'error', 'author_profile_link': 'error', 'author_bio': 'error', 'complete_content': 'error', })
            except Exception as e:
                print(f"Unexpected error: {e}")
                all_data.append({'title': 'error', 'link': 'error', 'date': 'error', 'author': 'error', 'author_profile_link': 'error', 'author_bio': 'error', 'complete_content': 'error', })
    except requests.RequestException as e:
        print(f"Request error for {link}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return all_data


doctor_list_all = []
for i in tqdm(range(1, 33)):
    print(f"Processing page {i}")
    try:
        url = f"https://www.rarediseaseadvisor.com/news/page/{i}/?junction=multiple-sclerosis"
        data = get_data(url)
        doctor_list_all.extend(data)
        print(f"Processed page {i+1}")
    except Exception as e:
        print(f"Error processing page {i+1}: {e}")

try:
    df = pd.DataFrame(doctor_list_all, columns=['title', 'link', 'date', 'author', 'author_profile_link', 'author_bio', 'complete_content'])
    df.to_excel('Output/rarediseaseadvisor_data.xlsx', index=False)
    print("Data saved successfully.")
except Exception as e:
    print(f"Error saving data to Excel: {e}")
