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
group_id = os.getenv("GroupID")
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
            
        if "/run" in data["text"].lower():
            main()

    return "ok", 200


# Function to fetch event data from GroupMe
def fetch_event_data(group_id, token):
    url = f"https://api.groupme.com/v3/groups/{group_id}/events?token={token}"
    response = requests.get(url)
    data = response.json()
    return data

# Function to tag people who have not RSVP'd
def tag_people_not_rsvpd(event_data, group_id, token):
    event_name = event_data['name']
    attendees = event_data['attendees']
    tagged_users = []
    
    # Get the list of group members
    members_url = f"https://api.groupme.com/v3/groups/{group_id}?token={token}"
    response = requests.get(members_url)
    members_data = response.json()
    members = members_data['response']['members']
    
    # Iterate over members and check RSVP status
    for member in members:
        member_id = member['user_id']
        member_name = member['nickname']
        
        # Check if the member has RSVP'd
        if member_id not in attendees:
            # Tag the member
            tagged_users.append(member_name)
    
    # Send a message tagging the users who have not RSVP'd
    if tagged_users:
        tagged_users_str = ', '.join(tagged_users)
        message = f"Hey everyone! Just a reminder for the upcoming event '{event_name}'. It seems that {tagged_users_str} have not RSVP'd yet. Please make sure to RSVP if you're planning to attend."
        send_message_to_group(group_id, token, message)

# Function to send a message to the group
def send_message_to_group(group_id, token, text):
    url = f"https://api.groupme.com/v3/groups/{group_id}/messages?token={access_token}"
    payload = {
        "message": {
            "source_guid": str(uuid.uuid4()),
            "text": text
        }
    }
    response = requests.post(url, json=payload)
    if response.status_code == 202:
        print("Message sent successfully!")
    else:
        print("Failed to send message.")

# Main function to fetch event data and tag people
def main():   
    # Fetch event data
    event_data = fetch_event_data(group_id, token)
    
    # Tag people who have not RSVP'd
    tag_people_not_rsvpd(event_data, group_id, token)


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
