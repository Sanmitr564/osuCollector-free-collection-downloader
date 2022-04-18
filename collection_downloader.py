from importlib.resources import path
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
#from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import os

COLLECTOR_BASE = "https://osucollector.com/collections/"
CHIMU_BASE = "https://api.chimu.moe/v1/download/"
API_URL = 'https://osu.ppy.sh/api/v2'
TOKEN_URL = 'https://osu.ppy.sh/oauth/token'
USER = os.environ.get('USERNAME')
PATH = f"C:/Users/{USER}/Downloads/"
CLIENT_ID =  #Put your client id(int)
CLIENT_SECRET =  #Put your Osu! api key(String)

def get_html(collection_number):

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(executable_path='./chromedriver', options=options)
    #driver.minimize_window()
    driver.get(COLLECTOR_BASE + str(collection_number))

    while True:
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        _html = driver.page_source
        _soup = BeautifulSoup(_html, "html.parser")
        
        if _soup.get_text().find("Nothing more to show.") != -1:
            break

    time.sleep(2)

    html = driver.page_source

    driver.close()

    return html

def get_beatmap_ids(html):
    soup = BeautifulSoup(html, "html.parser")

    map_profiles = soup.find_all(target="blank")

    id_list = []
    for map_profile in map_profiles:
        beatmap_id = int(map_profile.get('href')[28:])
        #print(beatmap_id)
        id_list.append(beatmap_id)
    return id_list

def get_token():
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials',
        'scope': 'public'
    }

    response = requests.post(TOKEN_URL, data=data)

    return response.json().get('access_token')

def get_beatmapset_ids(beatmap_ids):

    token = get_token()
    num_arrays = len(beatmap_ids) // 50
    num_arrays += 1 if len(beatmap_ids)%50 != 0 else 0
    id_arrays = []
    for i in range(num_arrays):
        id_arrays.append(beatmap_ids[i*50: (i+1) * 50])
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    beatmapset_id_set = set()

    for list in id_arrays:
        params = {
            'ids[]': list
        }
        response = requests.get(f'{API_URL}/beatmaps/',params=params, headers=headers)
        beatmapset_data = response.json().get('beatmaps')
        for element in beatmapset_data:
            beatmapset_id_set.add(element['beatmapset_id'])
    return beatmapset_id_set

def download_beatmapsets(beatmapset_ids, collection_number):
    directory = f'Collection {collection_number}'
    path = os.path.join(PATH, directory)
    os.mkdir(path)

    total = len(beatmapset_ids)
    undownloaded_beatmaps = []
    for i,beatmapset_id in enumerate(beatmapset_ids):
        progress = i+1
        print(f'Downloading beatmapset {progress}/{total}', end='\r')
        url = f'{CHIMU_BASE}{beatmapset_id}'
        complete_path = os.path.join(path, f'{beatmapset_id}.osz')
        r = requests.get(url, stream=True)
        if len(r.content) < 500:
            undownloaded_beatmaps.append(beatmapset_id)
        else:
            with open(complete_path, 'wb') as f:
                f.write(r.content)
        time.sleep(1)

    total_beatmapsets_downloaded = total - len(undownloaded_beatmaps)
    print(f'\nSuccessfully downloaded {total_beatmapsets_downloaded}/{total} beatmapsets')
    
    if len(undownloaded_beatmaps) > 0:
        print('Failed to download the following beatmapset(s)')
        for beatmapset in undownloaded_beatmaps:
            print(beatmapset)
    
    
if __name__ == '__main__':
    print('Please type the id of the collection you wish to download:')
    collection_id = int(input())
    
    html = get_html(collection_id)
    beatmap_ids = get_beatmap_ids(html)
    beatmapset_ids = get_beatmapset_ids(beatmap_ids)
    download_beatmapsets(beatmapset_ids,collection_id)
    print('Done!')