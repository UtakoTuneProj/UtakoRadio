import random
import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from xml.etree import ElementTree
from datetime import datetime as dt

import discord
import numpy as np
from numpy import linalg

from secrets import API_SECRET, TAG_BLACKLIST, POSITION_STEP, VERSION

client = discord.Client()
played = []
queue = []
positions = []
decode_nparray = lambda p: '[' + ','.join(map(lambda x: '{:.3}'.format(x), p)) + ']'

@client.event
async def on_ready():
    print('ready')

@client.event
async def on_message(message):
    global played
    global queue
    global positions
    channel = message.channel
    if message.author == client.user and message.content.startswith("Now playing in"):
        if queue:
            played += [queue.pop(0)]
        if len(played) > 100:
            del played[0:len(played)-100]
        await next_song()
    elif message.author != client.user:
        if message.content.startswith('!autoqueue') and message.author.top_role.name == 'admin':
            await next_song()
        if message.content.startswith('!resetposition') and message.author.top_role.name == 'admin':
            cmds = message.content.split()
            next_id = cmds[1] if len(cmds) > 1 else None

            tmp = positions
            positions = []
            try:
                await next_song(next_id)
            except ValueError:
                await client.send_message(channel, "specified id {} is inivalid".format(next_id))
                positions = tmp

def search_next_song():
    pos = get_nextpos()
    pos_url = decode_nparray(pos)
    req = Request('https://edge.utako-tune.jp/api/vocalosphere/point/?origin={p}&version={v}'.format(**{
        'p': pos_url,
        'v': VERSION,
    }))
    with urlopen(req) as res:
        results = json.loads(res.read().decode())['results']

    for result in results:
        next_id = result['id']
        if is_playable(next_id):
            break
        else:
            print('non playable {} was selected'.format(next_id))

    return next_id

async def next_song(next_id=None):
    global queue
    global positions

    if not next_id:
        next_id = search_next_song()

    try:
        movie_pos = get_moviepos(next_id)
    except HTTPError:
        raise ValueError('next_id {} is invalid'.format(next_id))
    except ValueError:
        raise ValueError('next_id {} is invalid'.format(next_id))

    queue.append(next_id)
    positions.append(movie_pos)
    movie_pos_url = decode_nparray(movie_pos)

    channel = client.get_channel('519408464208855058')
    await client.send_message(channel, "!play https://www.nicovideo.jp/watch/{}".format(next_id))
    print('queued {}'.format(next_id))

def get_nextpos():
    global positions
    if not positions:
        return np.array([random.random() * 2 - 1 for i in range(8)])

    if len(positions) == 1:
        vec = np.array([random.random() * 2 - 1 for i in range(8)])
    else:
        vec = positions[-1] - positions[-2]
        del position[0]

    vec = vec / linalg.norm(vec)
    return positions[-1] + POSITION_STEP * vec

def get_moviepos(mvid):
    req = Request('https://edge.utako-tune.jp/api/movie/{}'.format(mvid))
    with urlopen(req) as res:
        results = json.loads(res.read().decode())

    for songindex in results['songindex_set']:
        if songindex['version'] == VERSION:
            break
    else:
        raise ValueError('valid index not found')

    poslist = []
    for i in range(8):
        poslist.append(songindex['value{}'.format(i)])

    return np.array(poslist)

def is_playable(mvid):
    tree = {}

    if mvid in played + queue:
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
