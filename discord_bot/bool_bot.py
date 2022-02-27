#!/usr/bin/env python3

import json
import re
import os
import hvac
import boto3
import discord

#setup stuff
vault_client = hvac.Client(
    url=os.environ['VAULT_URL'],
    token=os.environ['VAULT_TOKEN']
)

res = vault_client.is_authenticated()
DISCORD_TOKEN = vault_client.secrets.kv.read_secret_version(path='discord_token')['data']['data']['key']
SPOTIFY_TOKEN1 = vault_client.secrets.kv.read_secret_version(path='spotify_token_1')['data']['data']['key']
SPOTIFY_TOKEN2 = vault_client.secrets.kv.read_secret_version(path='spotify_token_2')['data']['data']['key']
TEST_CHANNEL_ID = int(vault_client.secrets.kv.read_secret_version(path='test_channel_id')['data']['data']['key'])

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


#bot events
@client.event
async def on_ready():
    await client.get_channel(TEST_CHANNEL_ID).send('Updated. Am a brand new bot')


@client.event
async def on_message(message):
    if client.user.mentioned_in(message):
        message_content = message.content.lower()
        regex = r'\b(\w+ing)\b'
        if re.search(regex, message_content):
            word = re.findall(regex, message_content)[0]
            await message.channel.send(word.replace("ing", "ong").upper())
        elif 'lock' in message_content:
            if '-lock' in message_content:
                lock_server()
            elif '-unlock' in message_content:
                unlock_server()
        elif 'playlist_albums' in message_content:
            await bot_get_albums(message)
    elif 'https://clashfinder.com/m/' in message.content or 'https://clashfinder.com/s/' in message.content:
        await get_schedule(message)


#user defined functions
def call_bot_lambda(lambda_name, parameters):
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    response = lambda_client.invoke(
        FunctionName=lambda_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(parameters)
    )
    return response


#user defined functions
def lock_server():
    print('lock')
    return True


def unlock_server():
    print('unlock')
    return True


def create_embed(item, day):
    embed = discord.Embed(title=day, color=discord.Color.blue())
    dictionary = json.loads(item)['stage_schedules']
    stage_names = list(dictionary)
    for stage in stage_names:
        artist_string = ''
        for artist in dictionary[stage]['shows']:
            artist_string += artist + '\n'
        embed.add_field(name=stage, value=artist_string,
                        inline=True)
    return embed


#async functions
async def bot_get_albums(message):
    print('getting albums')
    response = call_bot_lambda("get_albums_lambda", {
        "playlist_url": message.content.split("playlist_albums ")[1],
        "spotify_tokens": [SPOTIFY_TOKEN1, SPOTIFY_TOKEN2]
    })
    for message_text in json.load(response['Payload']):
        await message.channel.send(message_text)
        print('message sent')


async def get_schedule(message):
    print('getting schedule')
    url = re.search("(?P<url>https?://[^\s]+)", message.content).group("url")
    response = call_bot_lambda("get_schedule_lambda", {
        "schedule_url": url
    })
    previous_day = ''
    for item in json.load(response['Payload']):
        json_item = json.loads(item)
        day = json_item['day']
        if previous_day == day:
            previous_day = day
            day += ' Cont.'
        else:
            previous_day = day
        await message.channel.send(embed=create_embed(item, day))


#start the bot
client.run(DISCORD_TOKEN)
