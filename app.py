import os
import requests
import bs4
import pandas as pd
import dataframe_image as dfi
from urllib.request import urlopen, Request

token = os.getenv("Token")
bot_id = os.getenv("BotID")
group_id = os.getenv("GroupID")

url = "https://api.groupme.com/v3/bots/post"
img_url = "https://image.groupme.com"
standings_url = "https://www.oaklandyard.com/lg_standings/lg_standings.asp?LgSessCode=2770&ReturnPg=lg%5Fsoccer%5Fcoed%2Easp%232770&ShowRankings=False&HeaderTitle=&sw=1800"

def fetch_standings_data(standings_url):
    response = requests.get(standings_url)
    response.raise_for_status()
    soup = bs4.BeautifulSoup(response.text)
    table = soup.find_all('div', {'class': 'divLargeTable'})[-1]
    rows = table.find_all('div', {'class': 'divMultipleColumns'})
    headers = ['W', 'L', 'T', 'S', 'A', 'D', 'P']
    databs = {}
    for row in rows[1:]:
        cols = row.find_all('div')
        index = cols[0].text.strip()
        databs[index] = [int(value.text) if value.text.isdigit() else 0 for value in cols[1:]]
    df = pd.DataFrame.from_dict(databs, orient='index', columns=headers)
    df['Color'] = df.index
    df.loc[df.index == 'The B Team', 'Color'] = 'Green'
    df.loc[df.index == '#BackHeelz', 'Color'] = 'Brown'
    df.loc[df.index == '5 North Sundowners', 'Color'] = 'Gray'
    df.loc[df.index == 'Misfits', 'Color'] = 'Blue'
    df.loc[df.index == 'Weak Ankles FC', 'Color'] = 'Black'
    df.loc[df.index == 'Killer Penguins', 'Color'] = 'Red'
    df.loc[df.index == 'Snax R Back', 'Color'] = 'Pink'
    df.loc[df.index == 'FC Beercelona', 'Color'] = 'Blue'
    df.loc[df.index == 'The Banshees', 'Color'] = 'Black'
    df.loc[df.index == 'Withourselves', 'Color'] = 'Yellow'
    df.loc[df.index == 'Off Daily', 'Color'] = 'Purple'
    df.loc[df.index == '', 'Color'] = ''
    df.loc[df.index == df['Color'], 'Color'] = '???'
    return df

def send_message(msg):
    json = {
        "bot_id": bot_id,
        "text": msg
    }
    req = requests.post(url, json=json)
    print("Message sent:", req.status_code)

def post_image_to_groupme(img_path):
    image = open(img_path, "rb").read()
    req = requests.post(
        url='https://image.groupme.com/pictures',
        data=image,
        headers={
            'Content-Type': 'image/png',
            'X-Access-Token': token
        }
    )
    try:
        d = req.json()
        picture_url = d["payload"]["picture_url"]
        send_json = {
            "bot_id": bot_id,
            "attachments": [
                {
                    "type": "image",
                    "url": picture_url
                }
            ]
        }
        r = requests.post(url=url
