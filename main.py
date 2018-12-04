import discord
import random
import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from xml.etree import ElementTree
from datetime import datetime as dt

from secrets import API_SECRET, TAG_BLACKLIST

client = discord.Client()
played = []
queue = []
positions = []

@client.event
async def on_ready():
    for _ in range(3):
        await next_song()
        time.sleep(20)

@client.event
async def on_message(message):
    global played
    global queue
    if message.author == client.user and message.content.startswith("Now playing in"):
        played += [queue.pop(0)]
        if len(played) > 100:
            del played[0:len(played)-100]
        await next_song()

async def next_song():
    global queue
    pos = '[' + ','.join(['{:.3}'.format( random.random() * 2 - 1 ) for i in range(8)]) + ']'
    req = Request('https://edge.utako-tune.jp/api/vocalosphere/point/?origin={}'.format(pos))
    with urlopen(req) as res:
        next_id = json.loads(res.read().decode())['results'][0]['id']

    if is_playable(next_id):
        queue.append(next_id)
        channel = client.get_channel('519408464208855058')
        await client.send_message(channel, "!play https://www.nicovideo.jp/watch/{}".format(next_id))
        print('queued {}'.format(next_id))
    else:
        print('non playable {} was selected'.format(next_id))
        await next_song()

def is_playable(mvid):
    tree = {}

    if mvid in played:
        return False

    req = Request('http://ext.nicovideo.jp/api/getthumbinfo/{}'.format(mvid))
    try:
        with urlopen(req) as response:
            root = ElementTree.fromstring(response.read())
    except HTTPError:
        return False

    if root.get('status') == 'ok':
        for child in root[0]:
            if child.tag == 'tags':
                tree['tags'] = set(x.text for x in child)
    else:
        return False

    if not tree['tags'].isdisjoint( TAG_BLACKLIST ):
        return False

    return True

client.run(API_SECRET)
