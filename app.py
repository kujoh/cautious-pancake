import os
import json
import requests
import random
from flask import Flask, request
import bs4
import pandas as pd
import numpy as np
import dataframe_image as dfi
import hashlib
from urllib.request import urlopen, Request

token = os.getenv("Token")
bot_id = os.getenv("BotID")
app = Flask(__name__)

url = "https://api.groupme.com/v3/bots/post"
img_url = "https://image.groupme.com"
standings_url = "https://www.oaklandyard.com/lg_standings/lg_standings.asp?LgSessCode=2770&ReturnPg=lg%5Fsoccer%5Fcoed%2Easp%232770&ShowRankings=False&HeaderTitle=&sw=1800"

@app.route("/", methods=["GET"])
def home():
    return "https://cautiouspancake.onrender.com"

@app.route("/", methods=["POST"])
def receive():

    data = request.get_json()
    print("Incoming Msg: ")
    print(data)

    # Prevent self-reply
    if data["sender_type"] != "bot":
        if "/help" in data["text"].lower():     #if data["text"].startswith("/help"):
            send(" Hi, " + data["name"] + ". \n\nAll I do right now is pull the current standings. If a message sent to this group includes \"/standings\", I will post them.")

        if "/standings" in data["text"].lower():     #if data["text"].startswith("/standings"):
            df = fetch_standings_data(standings_url)
            dfi.export(df, 'standings.png', table_conversion = 'matplotlib')
            post_img_to_groupme(
                "standings.png")
            
        if "/colors" in data["text"].lower():
            df = fetch_standings_data(standings_url)
            dfi.export(df['Color'], 'colors.png', table_conversion = 'matplotlib')
            post_img_to_groupme(
                "colors.png")

    return "ok", 200

def fetch_standings_data(standings_url):
    response = requests.get(standings_url)
    response.raise_for_status()
    soup = bs4.BeautifulSoup(response.text)
    # Find everything with class divLargeTable and assign to table
    table = soup.find_all('div', {'class': 'divLargeTable'})[-1]
    # Find everything with class divMultipleColumns and assign to rows
    rows = table.find_all('div', {'class': 'divMultipleColumns'})
    # Assign standingsTitle1 as headers
    headers = [title.text for title in rows[0].find_all('div', {'class': 'standingsTitle1'})]

    databs = {}
    for row in rows[1:]:
        cols = row.find_all('div')
        index = cols[0].text.strip()
        databs[index] = [int(value.text) if value.text.isdigit() else 0 for value in cols[1:]]

    df = pd.DataFrame.from_dict(databs, orient='index', columns=headers)

    # Add a new column and set its value based on a condition wrt the index
    df['Color'] = df.index
    df.loc[df.index == 'The B Team', 'Color'] = 'Green'
    df.loc[df.index == '#BackHeelz', 'Color'] = 'Brown'
    df.loc[df.index == '5 North Sundowners', 'Color'] = 'Gray'
    df.loc[df.index == 'Misfits', 'Color'] = 'Blue'
    df.loc[df.index == 'Weak Ankles FC', 'Color'] = 'Black'
    df.loc[df.index == '', 'Color'] = ''
    df.loc[df.index == df['Color'], 'Color'] = '???'

    return df

def send(msg):
    json = {
        "bot_id": bot_id,
        "text": msg
    }
    req = requests.post(url, json=json)
    print("send complete: ", req)


def post_img_to_groupme(img):
    image = open(img, "rb").read()
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
    except (json.JSONDecodeError, KeyError) as e:
        print("Error decoding JSON response:", e)
        return

    send_json = {
        "bot_id": bot_id,
        "attachments": [
            {
                "type": "image",
                "url": picture_url
            }
        ]
    }

    r = requests.post(url=url, json=send_json)
    print("post_img_to_groupme complete:", r)
